from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from mediascan import Genre

"""
Note: I used this script to generate some of the genre cluster links
It's only based on the genre name (e.g. "Classic Rock"), not the quality 
of the music, so it's not very good, e.g. it groups "Glam Rock" with "Goth Rock", 
so some manual editing was still required. Otherwise this code could be 
integrated into the app. Nonetheless the script was very helpful and could
easily be repurposed for myriad other uses.
TODO: Research more advanced forms of genre classification and introduce
genre tag-checking or auto-tagging feature.
"""

# List of genres
genres = list(Genre)

# Convert genres into numerical vectors using TF-IDF
vectorizer = TfidfVectorizer(stop_words="english")
X = vectorizer.fit_transform(genres)

N_CLUSTERS = 16
# Fit the KMeans clustering algorithm
kmeans = KMeans(n_clusters=16, random_state=42)
kmeans.fit(X)

# Get the clusters assigned to each genre
clusters = kmeans.labels_

# Create a dictionary to map genres to their clusters
clustered_genres = {i: [] for i in range(N_CLUSTERS)}
for genre, cluster in zip(genres, clusters):
    clustered_genres[cluster].append(genre)

# Print the clustered genres
for cluster, cluster_genres in clustered_genres.items():
    print(f"Cluster {cluster}:")
    print("[" + ", ".join([f"'{c}'" for c in cluster_genres]) + "]")
    print()
