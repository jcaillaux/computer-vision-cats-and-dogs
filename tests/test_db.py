#!/usr/bin/env python3
"""Tests pytest des fonctions de base de données"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from sqlmodel import Session, create_engine, text
from sqlalchemy import URL
from sqlalchemy.exc import IntegrityError
import uuid as uuid_lib
from config.settings import PG_CONFIG
import os

# Ajouter le répertoire racine au path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.database.db import (
    make_engine, create_tables, drop_tables, insert,
    insert_feedback, update_feedback, insert_image_metadata, insert_prediction
)
from src.database.models import Feedback, ImageMetadata, PredictionLog, get_utc_timestamp

# Configuration de test - utiliser une base de données de test
TEST_DB_CONFIG = PG_CONFIG
#TEST_DB_CONFIG["database"] = "cats_dogs_test"

def get_test_engine():
    """Crée un moteur de test"""
    test_db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=TEST_DB_CONFIG["user"],
        password=TEST_DB_CONFIG["password"],
        host=TEST_DB_CONFIG["host"],
        port=TEST_DB_CONFIG["port"],
        database=TEST_DB_CONFIG["database"],
    )
    
    return create_engine(test_db_url, echo=True)

class TestTableCreation:
    """Tests de création de tables uniquement"""
    
    def test_engine_creation(self):
        """Test que l'on peut créer un moteur de base de données"""
        engine = get_test_engine()
        assert engine is not None
        
        # Test de connexion basique
        with Session(engine) as session:
            result = session.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    
    def test_create_tables_function_exists(self):
        """Test que la fonction create_tables existe et peut être appelée"""
        with patch('src.database.db.make_engine', return_value=get_test_engine()):
            # Ne devrait pas lever d'exception
            create_tables()
    
    def test_drop_tables_function_exists(self):
        """Test que la fonction drop_tables existe et peut être appelée"""
        with patch('src.database.db.make_engine', return_value=get_test_engine()):
            # D'abord créer les tables
            create_tables()
            # Puis les supprimer - ne devrait pas lever d'exception
            drop_tables()
    
    def test_tables_actually_created(self):
        """Test que les tables sont vraiment créées dans la base"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Nettoyer d'abord
            try:
                drop_tables()
            except:
                pass  # Ignore si les tables n'existent pas
            
            # Créer les tables
            create_tables()
            
            # Vérifier que les tables existent
            with Session(engine) as session:
                # Query pour lister les tables
                result = session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('feedback', 'imagemetadata', 'predictionlog')
                """))
                
                tables = [row[0] for row in result.fetchall()]
                
                # Vérifier que nos 3 tables sont présentes
                expected_tables = ['feedback', 'imagemetadata', 'predictionlog']
                for table in expected_tables:
                    assert table in tables, f"Table {table} n'a pas été créée"
                
                print(f"Tables créées avec succès: {tables}")
    
    def test_models_have_correct_structure(self):
        """Test que les modèles ont la structure correcte"""
        # Test des classes de modèles
        assert hasattr(Feedback, 'uuid')
        assert hasattr(Feedback, 'timestamp') 
        assert hasattr(Feedback, 'grade')
        
        assert hasattr(ImageMetadata, 'hash')
        assert hasattr(ImageMetadata, 'filename')
        assert hasattr(ImageMetadata, 'ext_type')
        
        assert hasattr(PredictionLog, 'uuid')
        assert hasattr(PredictionLog, 'prob_cat')
        assert hasattr(PredictionLog, 'prob_dog')
        assert hasattr(PredictionLog, 'inference_time_ms')
        assert hasattr(PredictionLog, 'success')
        
        print("Toutes les structures de modèles sont correctes")
    
    def test_table_columns_exist(self):
        """Test que les colonnes des tables existent comme attendu"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # S'assurer que les tables existent
            create_tables()
            
            with Session(engine) as session:
                # Test table feedback
                result = session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'feedback'
                """))
                feedback_columns = [row[0] for row in result.fetchall()]
                assert 'uuid' in feedback_columns
                assert 'timestamp' in feedback_columns
                assert 'grade' in feedback_columns
                
                # Test table imagemetadata  
                result = session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'imagemetadata'
                """))
                image_columns = [row[0] for row in result.fetchall()]
                assert 'hash' in image_columns
                assert 'filename' in image_columns
                
                # Test table predictionlog
                result = session.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'predictionlog'
                """))
                prediction_columns = [row[0] for row in result.fetchall()]
                assert 'uuid' in prediction_columns
                assert 'prob_cat' in prediction_columns
                assert 'prob_dog' in prediction_columns
                
                print("Toutes les colonnes sont présentes")

def verify_in_database(engine, table_name, primary_key_field, primary_key_value, expected_data):
    """Helper to verify data directly in the database"""
    with Session(engine) as session:
        result = session.execute(
            text(f"SELECT * FROM {table_name} WHERE {primary_key_field} = :pk"),
            {"pk": primary_key_value}
        )
        row = result.fetchone()
        if row is None:
            return False, "Row not found"
        
        # Verify each expected field
        for field, expected_value in expected_data.items():
            actual_value = getattr(row, field)
            if actual_value != expected_value:
                return False, f"{field}: expected {expected_value}, got {actual_value}"
        
        return True, row

class TestImageMetadataInsert:
    """Tests pour l'insertion de métadonnées d'image"""
    
    @pytest.fixture(autouse=True)
    def setup_tables(self):
        """Setup: créer les tables avant chaque test, nettoyer après"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Nettoyer et recréer les tables
            try:
                drop_tables()
            except:
                pass  # Ignore si les tables n'existent pas
            create_tables()
        
        yield  # Le test s'exécute ici
        
        # Teardown: nettoyer les données après le test
        with Session(engine) as session:
            try:
                # Supprimer toutes les données de test
                session.execute(text("DELETE FROM imagemetadata WHERE hash LIKE 'test_%'"))
                session.commit()
            except:
                pass  # Ignore les erreurs de cleanup
    
    def test_insert_image_metadata_basic(self):
        """Test d'insertion basique de métadonnées d'image"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Données de test
            test_data = {
                "hash": "test_hash_basic",
                "filename": "test_image.jpg",
                "ext_type": "jpg",
                "size_w": 224,
                "size_h": 224,
                "color_mode": "RGB"
            }
            
            # Insérer les données
            result = insert_image_metadata(**test_data)
            
            # Vérification basique - l'objet existe
            assert result is not None
            
            # Vérifier directement dans la base de données pour éviter DetachedInstanceError
            success, db_row = verify_in_database(
                engine, 
                "imagemetadata", 
                "hash", 
                test_data["hash"],
                test_data
            )
            
            assert success, f"Database verification failed: {db_row}"
            assert db_row.hash == test_data["hash"]
            assert db_row.filename == test_data["filename"]
            assert db_row.ext_type == test_data["ext_type"]
            
            print(f"✓ Image metadata inserted and verified: {test_data['filename']}")
    
    def test_insert_image_metadata_in_database(self):
        """Test que les données sont vraiment insérées dans la base"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Données de test
            test_data = {
                "hash": "test_hash_db_check",
                "filename": "database_test.png",
                "ext_type": "png", 
                "size_w": 512,
                "size_h": 512,
                "color_mode": "RGBA"
            }
            
            # Insérer les données
            insert_image_metadata(**test_data)
            
            # Vérifier dans la base de données
            with Session(engine) as session:
                # Récupérer l'enregistrement
                result = session.execute(
                    text("SELECT * FROM imagemetadata WHERE hash = :hash"),
                    {"hash": test_data["hash"]}
                )
                row = result.fetchone()
                
                assert row is not None, "L'enregistrement n'a pas été trouvé dans la base"
                
                # Vérifier chaque champ (accès par nom de colonne)
                assert row.hash == test_data["hash"]
                assert row.filename == test_data["filename"]
                assert row.ext_type == test_data["ext_type"]
                assert row.size_w == test_data["size_w"]
                assert row.size_h == test_data["size_h"]
                assert row.color_mode == test_data["color_mode"]
                
                print(f"✓ Data verified in database: {row.filename}")
    
    def test_insert_image_metadata_different_formats(self):
        """Test d'insertion avec différents formats d'image"""
        test_cases = [
            {
                "hash": "test_jpg_format",
                "filename": "photo.jpg",
                "ext_type": "jpg",
                "size_w": 1920,
                "size_h": 1080,
                "color_mode": "RGB"
            },
            {
                "hash": "test_png_format", 
                "filename": "graphic.png",
                "ext_type": "png",
                "size_w": 800,
                "size_h": 600,
                "color_mode": "RGBA"
            },
            {
                "hash": "test_gif_format",
                "filename": "animation.gif", 
                "ext_type": "gif",
                "size_w": 256,
                "size_h": 256,
                "color_mode": "P"
            }
        ]
        
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            for i, test_data in enumerate(test_cases):
                result = insert_image_metadata(**test_data)
                
                assert result is not None
                
                # Vérifier dans la base de données
                success, db_row = verify_in_database(
                    engine,
                    "imagemetadata",
                    "hash", 
                    test_data["hash"],
                    test_data
                )
                
                assert success, f"Database verification failed for {test_data['ext_type']}: {db_row}"
                
                print(f"✓ Format {i+1}/{len(test_cases)} inserted: {test_data['ext_type'].upper()}")
    
    def test_insert_image_metadata_duplicate_hash(self):
        """Test d'insertion avec hash dupliqué (devrait être géré par rollback)"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Données de test
            test_data = {
                "hash": "test_duplicate_hash",
                "filename": "original.jpg",
                "ext_type": "jpg",
                "size_w": 100,
                "size_h": 100,
                "color_mode": "RGB"
            }
            
            # Première insertion - devrait réussir
            result1 = insert_image_metadata(**test_data)
            assert result1 is not None
            
            # Vérifier que la première insertion a réussi
            success1, db_row1 = verify_in_database(
                engine, "imagemetadata", "hash", test_data["hash"], test_data
            )
            assert success1, "First insertion should succeed"
            print("✓ First insertion successful")
            
            # Deuxième insertion avec même hash mais données différentes
            test_data_duplicate = test_data.copy()
            test_data_duplicate["filename"] = "duplicate.jpg"
            test_data_duplicate["size_w"] = 200
            
            # Ne devrait pas lever d'exception (géré par rollback)
            result2 = insert_image_metadata(**test_data_duplicate)
            assert result2 is not None  # L'objet est créé même si pas inséré
            
            # Vérifier que les données originales sont toujours là (pas écrasées)
            with Session(engine) as session:
                result = session.execute(
                    text("SELECT filename, size_w FROM imagemetadata WHERE hash = :hash"),
                    {"hash": test_data["hash"]}
                )
                row = result.fetchone()
                assert row is not None
                # Devrait garder les données originales, pas les nouvelles
                assert row.filename == "original.jpg"  # Pas "duplicate.jpg"
                assert row.size_w == 100  # Pas 200
            
            print("✓ Duplicate hash handled gracefully - original data preserved")
    
    def test_insert_image_metadata_large_dimensions(self):
        """Test avec des dimensions d'image importantes"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_data = {
                "hash": "test_large_image",
                "filename": "huge_photo.jpg",
                "ext_type": "jpg",
                "size_w": 4096,
                "size_h": 4096,
                "color_mode": "RGB"
            }
            
            result = insert_image_metadata(**test_data)
            assert result is not None
            
            # Vérifier directement dans la base
            success, db_row = verify_in_database(
                engine, "imagemetadata", "hash", test_data["hash"], test_data
            )
            assert success, f"Large dimensions verification failed: {db_row}"
            assert db_row.size_w == 4096
            assert db_row.size_h == 4096
            
            print("✓ Large dimensions handled correctly")
    
    def test_insert_image_metadata_special_characters(self):
        """Test avec des caractères spéciaux dans le nom de fichier"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_data = {
                "hash": "test_special_chars",
                "filename": "éàü_image-test (1).jpg",
                "ext_type": "jpg",
                "size_w": 300,
                "size_h": 200,
                "color_mode": "RGB"
            }
            
            result = insert_image_metadata(**test_data)
            assert result is not None
            
            # Vérifier directement dans la base
            success, db_row = verify_in_database(
                engine, "imagemetadata", "hash", test_data["hash"], test_data
            )
            assert success, f"Special characters verification failed: {db_row}"
            assert db_row.filename == "éàü_image-test (1).jpg"
            
            print("✓ Special characters handled correctly")
    
    @pytest.mark.parametrize("ext_type,color_mode", [
        ("jpg", "RGB"),
        ("png", "RGBA"), 
        ("gif", "P"),
        ("bmp", "RGB"),
        ("tiff", "CMYK")
    ])
    def test_insert_image_metadata_parametrized(self, ext_type, color_mode):
        """Test paramétré avec différentes combinaisons ext_type/color_mode"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_data = {
                "hash": f"test_param_{ext_type}_{color_mode}",
                "filename": f"test.{ext_type}",
                "ext_type": ext_type,
                "size_w": 400,
                "size_h": 300,
                "color_mode": color_mode
            }
            
            result = insert_image_metadata(**test_data)
            assert result is not None
            
            # Vérifier directement dans la base
            success, db_row = verify_in_database(
                engine, "imagemetadata", "hash", test_data["hash"], test_data
            )
            assert success, f"Parametrized test failed for {ext_type}/{color_mode}: {db_row}"
            assert db_row.ext_type == ext_type
            assert db_row.color_mode == color_mode
            
            print(f"✓ {ext_type.upper()}/{color_mode} combination works")

class TestPredictionLogInsert:
    """Tests pour l'insertion de logs de prédiction"""
    
    @pytest.fixture(autouse=True)
    def setup_tables(self):
        """Setup: créer les tables et données nécessaires avant chaque test"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Nettoyer et recréer les tables
            try:
                drop_tables()
            except:
                pass
            create_tables()
            
            # Créer une image de référence pour les tests de prédiction
            self.test_image_data = {
                "hash": "test_prediction_image",
                "filename": "prediction_test.jpg",
                "ext_type": "jpg",
                "size_w": 224,
                "size_h": 224,
                "color_mode": "RGB"
            }
            insert_image_metadata(**self.test_image_data)
        
        yield engine
        
        # Teardown: nettoyer les données de test
        with Session(engine) as session:
            try:
                session.execute(text("DELETE FROM predictionlog WHERE uuid LIKE 'test_%'"))
                session.execute(text("DELETE FROM imagemetadata WHERE hash LIKE 'test_%'"))
                session.commit()
            except:
                pass
    
    def test_insert_prediction_success(self, setup_tables):
        """Test d'insertion réussie de log de prédiction"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Données de prédiction de test
            test_uuid = "test_pred_success"
            prediction_data = {
                "p_cat": 0.7,
                "p_dog": 0.3
            }
            
            result = insert_prediction(
                uuid=test_uuid,
                image_id=self.test_image_data["hash"],
                inference_time_ms=150.5,
                success=True,
                prediction=prediction_data
            )
            
            assert result is not None
            
            # Vérifier directement dans la base de données
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT * FROM predictionlog WHERE uuid = :uuid"),
                    {"uuid": test_uuid}
                )
                row = db_result.fetchone()
                
                assert row is not None
                assert row.uuid == test_uuid
                assert row.prob_cat == 0.7
                assert row.prob_dog == 0.3
                assert row.inference_time_ms == 150.5
                assert row.success is True
                assert row.image_id == self.test_image_data["hash"]
                
                print(f"✓ Prediction log inserted successfully: {test_uuid}")
    
    def test_insert_prediction_with_failure(self, setup_tables):
        """Test d'insertion avec échec de prédiction"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_uuid = "test_pred_failure"
            prediction_data = {
                "p_cat": None,
                "p_dog": None
            }
            
            result = insert_prediction(
                uuid=test_uuid,
                image_id=self.test_image_data["hash"],
                inference_time_ms=25.0,
                success=False,
                prediction=prediction_data
            )
            
            assert result is not None
            
            # Vérifier dans la base de données
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT * FROM predictionlog WHERE uuid = :uuid"),
                    {"uuid": test_uuid}
                )
                row = db_result.fetchone()
                
                assert row is not None
                assert row.success is False
                assert row.prob_cat is None
                assert row.prob_dog is None
                assert row.inference_time_ms == 25.0
                
                print("✓ Failed prediction log handled correctly")
    
    def test_insert_prediction_missing_image(self, setup_tables):
        """Test d'insertion avec image_id inexistant (devrait être géré par rollback)"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_uuid = "test_pred_no_image"
            prediction_data = {"p_cat": 0.5, "p_dog": 0.5}
            
            # Ne devrait pas lever d'exception (géré par rollback)
            result = insert_prediction(
                uuid=test_uuid,
                image_id="nonexistent_hash",
                inference_time_ms=100.0,
                success=True,
                prediction=prediction_data
            )
            
            assert result is not None  # Objet créé même si pas inséré
            
            # Vérifier que l'insertion n'a pas eu lieu
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT COUNT(*) as count FROM predictionlog WHERE uuid = :uuid"),
                    {"uuid": test_uuid}
                )
                count = db_result.fetchone().count
                
                # Devrait être 0 car rollback
                assert count == 0
                
                print("✓ Missing image foreign key handled by rollback")
    
    @pytest.mark.parametrize("cat_prob,dog_prob", [
        (1.0, 0.0),    # Certain cat
        (0.0, 1.0),    # Certain dog  
        (0.5, 0.5),    # Uncertain
        (0.9, 0.1),    # High confidence cat
        (0.1, 0.9),    # High confidence dog
    ])
    def test_insert_prediction_different_probabilities(self, setup_tables, cat_prob, dog_prob):
        """Test paramétré avec différentes probabilités"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            test_uuid = f"test_pred_prob_{cat_prob}_{dog_prob}"
            prediction_data = {
                "p_cat": cat_prob,
                "p_dog": dog_prob
            }
            
            result = insert_prediction(
                uuid=test_uuid,
                image_id=self.test_image_data["hash"],
                inference_time_ms=75.0,
                success=True,
                prediction=prediction_data
            )
            
            assert result is not None
            
            # Vérifier dans la base de données
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT prob_cat, prob_dog FROM predictionlog WHERE uuid = :uuid"),
                    {"uuid": test_uuid}
                )
                row = db_result.fetchone()
                
                assert row is not None
                assert row.prob_cat == cat_prob
                assert row.prob_dog == dog_prob
                
                print(f"✓ Probabilities {cat_prob}/{dog_prob} handled correctly")
    
    def test_insert_prediction_various_inference_times(self, setup_tables):
        """Test avec différents temps d'inférence"""
        engine = setup_tables
        inference_times = [10.5, 50.0, 100.25, 250.75, 500.0, 1000.0]
        
        with patch('src.database.db.make_engine', return_value=engine):
            for i, inference_time in enumerate(inference_times):
                test_uuid = f"test_pred_time_{i}"
                prediction_data = {"p_cat": 0.6, "p_dog": 0.4}
                
                result = insert_prediction(
                    uuid=test_uuid,
                    image_id=self.test_image_data["hash"],
                    inference_time_ms=inference_time,
                    success=True,
                    prediction=prediction_data
                )
                
                assert result is not None
                
                # Vérifier le temps d'inférence
                with Session(engine) as session:
                    db_result = session.execute(
                        text("SELECT inference_time_ms FROM predictionlog WHERE uuid = :uuid"),
                        {"uuid": test_uuid}
                    )
                    row = db_result.fetchone()
                    assert row.inference_time_ms == inference_time
                
                print(f"✓ Inference time {inference_time}ms handled correctly")

class TestFeedbackInsertUpdate:
    """Tests pour l'insertion et mise à jour de feedback"""
    
    @pytest.fixture(autouse=True) 
    def setup_tables(self):
        """Setup: créer les tables et données nécessaires"""
        engine = get_test_engine()
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Nettoyer et recréer les tables
            try:
                drop_tables()
            except:
                pass
            create_tables()
            
            # Créer image et prédiction de référence
            self.test_image_data = {
                "hash": "test_feedback_image",
                "filename": "feedback_test.jpg", 
                "ext_type": "jpg",
                "size_w": 224,
                "size_h": 224,
                "color_mode": "RGB"
            }
            insert_image_metadata(**self.test_image_data)
            
            self.test_uuid = "test_feedback_prediction"
            prediction_data = {"p_cat": 0.8, "p_dog": 0.2}
            insert_prediction(
                uuid=self.test_uuid,
                image_id=self.test_image_data["hash"],
                inference_time_ms=100.0,
                success=True,
                prediction=prediction_data
            )
        
        yield engine
        
        # Teardown
        with Session(engine) as session:
            try:
                session.execute(text("DELETE FROM feedback WHERE uuid LIKE 'test_%'"))
                session.execute(text("DELETE FROM predictionlog WHERE uuid LIKE 'test_%'"))
                session.execute(text("DELETE FROM imagemetadata WHERE hash LIKE 'test_%'"))
                session.commit()
            except:
                pass
    
    def test_insert_feedback_success(self, setup_tables):
        """Test d'insertion réussie de feedback"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            result = insert_feedback(uuid=self.test_uuid, grade=5)
            
            assert result is not None
            
            # Vérifier dans la base de données
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT * FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                row = db_result.fetchone()
                
                assert row is not None
                assert row.uuid == self.test_uuid
                assert row.grade == 5
                assert row.timestamp is not None
                
                print(f"✓ Feedback inserted successfully: grade {row.grade}")
    
    def test_update_feedback_success(self, setup_tables):
        """Test de mise à jour réussie de feedback"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Insérer le feedback initial
            insert_feedback(uuid=self.test_uuid, grade=3)
            
            # Récupérer le timestamp initial
            with Session(engine) as session:
                initial_result = session.execute(
                    text("SELECT timestamp FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                initial_timestamp = initial_result.fetchone().timestamp
            
            # Attendre un peu pour s'assurer que le timestamp change
            import time
            time.sleep(0.1)
            
            # Mettre à jour le feedback
            update_feedback(uuid=self.test_uuid, grade=5)
            
            # Vérifier la mise à jour
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT * FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                row = db_result.fetchone()
                
                assert row is not None
                assert row.grade == 5  # Grade mis à jour
                assert row.timestamp > initial_timestamp  # Timestamp mis à jour
                
                print(f"✓ Feedback updated successfully: grade 3 → {row.grade}")
    
    def test_update_feedback_not_found(self, setup_tables):
        """Test de mise à jour de feedback inexistant"""
        with patch('src.database.db.make_engine', return_value=setup_tables):
            nonexistent_uuid = "test_nonexistent_feedback"
            
            with pytest.raises(ValueError, match=f"Feedback with id {nonexistent_uuid} not found"):
                update_feedback(uuid=nonexistent_uuid, grade=5)
            
            print("✓ Update non-existent feedback raises ValueError correctly")
    
    def test_insert_feedback_missing_prediction(self, setup_tables):
        """Test d'insertion de feedback avec UUID de prédiction inexistant"""
        with patch('src.database.db.make_engine', return_value=setup_tables):
            nonexistent_uuid = "test_no_prediction"
            
            # Ne devrait pas lever d'exception (géré par rollback)
            result = insert_feedback(uuid=nonexistent_uuid, grade=4)
            assert result is not None
            
            # Vérifier que l'insertion n'a pas eu lieu
            with Session(setup_tables) as session:
                db_result = session.execute(
                    text("SELECT COUNT(*) as count FROM feedback WHERE uuid = :uuid"),
                    {"uuid": nonexistent_uuid}
                )
                count = db_result.fetchone().count
                assert count == 0
                
                print("✓ Missing prediction foreign key handled by rollback")
    
    @pytest.mark.parametrize("grade", [1, 2, 3, 4, 5])
    def test_feedback_different_grades(self, setup_tables, grade):
        """Test paramétré avec différentes valeurs de grade"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            # Créer une prédiction unique pour chaque grade
            test_uuid = f"test_grade_{grade}"
            prediction_data = {"p_cat": 0.5, "p_dog": 0.5}
            insert_prediction(
                uuid=test_uuid,
                image_id=self.test_image_data["hash"],
                inference_time_ms=100.0,
                success=True,
                prediction=prediction_data
            )
            
            # Insérer le feedback
            result = insert_feedback(uuid=test_uuid, grade=grade)
            assert result is not None
            
            # Vérifier dans la base de données
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT grade FROM feedback WHERE uuid = :uuid"),
                    {"uuid": test_uuid}
                )
                row = db_result.fetchone()
                assert row.grade == grade
                
                print(f"✓ Grade {grade} handled correctly")
    
    def test_feedback_workflow_complete(self, setup_tables):
        """Test du workflow complet: insert → update → update"""
        engine = setup_tables
        
        with patch('src.database.db.make_engine', return_value=engine):
            # 1. Insérer feedback initial
            insert_feedback(uuid=self.test_uuid, grade=2)
            
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT grade FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                assert db_result.fetchone().grade == 2
            
            # 2. Première mise à jour
            update_feedback(uuid=self.test_uuid, grade=4)
            
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT grade FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                assert db_result.fetchone().grade == 4
            
            # 3. Deuxième mise à jour
            update_feedback(uuid=self.test_uuid, grade=5)
            
            with Session(engine) as session:
                db_result = session.execute(
                    text("SELECT grade FROM feedback WHERE uuid = :uuid"),
                    {"uuid": self.test_uuid}
                )
                assert db_result.fetchone().grade == 5
                
                print("✓ Complete feedback workflow: insert(2) → update(4) → update(5)")

if __name__ == "__main__":
    # Permettre l'exécution directe du fichier
    pytest.main([__file__, "-v", "-s"])