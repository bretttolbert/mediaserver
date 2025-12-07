from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

from mediascan import Genre

"""
Note: I used this script to generate some of the genre cluster links
It's only based on the genre name, not the quality of the music, so
it's not very good, e.g. it groups "Glam Rock" with "Goth Rock", etc.
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
