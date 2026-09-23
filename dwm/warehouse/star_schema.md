# Mini Spotify Star Schema

```text
                         dim_user
                            |
                            |
                            v
dim_date ---------> fact_listening <--------- dim_song
                            |                     |
                            |                     |
                            v                     |
                       dim_artist <---------------+
                            |
                            |
                            v
                        dim_genre