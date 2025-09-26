# Stratégie de réentrainement

Les performances du modèles de classification sont suivies en temps réel grâce à des indicateurs stocké automatiquement en base de données. Certains de ces indicateurs peuvent être visualisés à l'aide d'un dashboard Grafana.

Les performances du services de classifications sont principalements évaluées à l'aide du temps de réponse du point de termianaison *predict* ainsi que du taux de satisfaction evalué comme une moyenne des avis poisitif et négatifs. Puisque des retours ne sont pas systèmatiquement donnés le taux de satisfaction n'est significatifs que si le taux de participation est sufficamment élevé.

Afin de décider d'une mise à jour du modèle, un seuil critique de satisfaction - fixé arbitrairement à 80 % - et conditioné à un taux de participation - d'au moins  10% - pourcent doit motivé un agent à investiguer les causes potentielles de cette perte supposée de performance et de déterminer si cette dernièe est une dégradation des performances sur données hors distribution.

Pour cela, à chaque soumission des données sur l'image à savoir son hash md5, le nombre de cannaux de couleur, la resolution ainsi que le type d'image sont stocké. Dans ce cas le jeu d'entrainement doit être compléter avec des données correctement labélisées ayant des caractéristiques proches des image associée à des feedback négatifs.

***Remarque 1 : il faut s'assurer que les feedbacks négatifs ne sont pas du à une sous-performance de l'infrastructure (cf. temps de réponse < 200 ms)***

***Remarque 2 : Les images soumises ne sont pas stockés. Si elle le sont dans le future elles ne doivent pas être utilisées pour augmenter le jeu d'entraienement afin d'améliorer artificiellement les performances du modèle.***