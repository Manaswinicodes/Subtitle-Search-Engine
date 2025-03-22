import sqlite3
import zipfile
import io
import os
from datetime import datetime

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Create database connection
conn = sqlite3.connect('data/eng_subtitles_database.db')
cursor = conn.cursor()

# Create table
cursor.execute('''
CREATE TABLE IF NOT EXISTS zipfiles (
    num INTEGER PRIMARY KEY,
    name TEXT,
    content BLOB
)
''')

# Sample subtitle data
sample_subtitles = [
    {
        'id': 1001,
        'name': 'The Shawshank Redemption (1994)',
        'text': '''1
00:00:10,000 --> 00:00:15,000
I believe in two things: discipline and the Bible.

2
00:00:16,000 --> 00:00:21,000
Here you'll receive both. Put your trust in the Lord.

3
00:00:23,000 --> 00:00:28,000
Your ass belongs to me. Welcome to Shawshank.

4
00:00:30,000 --> 00:00:35,000
Get busy living or get busy dying. That's goddamn right.

5
00:00:37,000 --> 00:00:42,000
I have to remind myself that some birds aren't meant to be caged.
'''
    },
    {
        'id': 1002,
        'name': 'The Godfather (1972)',
        'text': '''1
00:00:10,000 --> 00:00:15,000
I'm gonna make him an offer he can't refuse.

2
00:00:16,000 --> 00:00:21,000
It's not personal, Sonny. It's strictly business.

3
00:00:23,000 --> 00:00:28,000
Leave the gun. Take the cannoli.

4
00:00:30,000 --> 00:00:35,000
A man who doesn't spend time with his family can never be a real man.

5
00:00:37,000 --> 00:00:42,000
Great men are not born great, they grow great.
'''
    },
    {
        'id': 1003,
        'name': 'The Dark Knight (2008)',
        'text': '''1
00:00:10,000 --> 00:00:15,000
Why so serious?

2
00:00:16,000 --> 00:00:21,000
Some men just want to watch the world burn.

3
00:00:23,000 --> 00:00:28,000
You either die a hero or live long enough to see yourself become the villain.

4
00:00:30,000 --> 00:00:35,000
The night is darkest just before the dawn.

5
00:00:37,000 --> 00:00:42,000
This city just showed you that it's full of people ready to believe in good.
'''
    },
    {
        'id': 1004,
        'name': 'Pulp Fiction (1994)',
        'text': '''1
00:00:10,000 --> 00:00:15,000
Royale with cheese.

2
00:00:16,000 --> 00:00:21,000
Say what again. Say what again, I dare you, I double-dare you.

3
00:00:23,000 --> 00:00:28,000
The path of the righteous man is beset on all sides by the inequities of the selfish.

4
00:00:30,000 --> 00:00:35,000
Zed's dead, baby. Zed's dead.

5
00:00:37,000 --> 00:00:42,000
I'm not a hero. I'm not a bad guy. I'm just an old man who's been in the business a long time.
'''
    },
    {
        'id': 1005,
        'name': 'Forrest Gump (1994)',
        'text': '''1
00:00:10,000 --> 00:00:15,000
Life is like a box of chocolates. You never know what you're gonna get.

2
00:00:16,000 --> 00:00:21,000
Stupid is as stupid does.

3
00:00:23,000 --> 00:00:28,000
Run, Forrest, run!

4
00:00:30,000 --> 00:00:35,000
That's all I have to say about that.

5
00:00:37,000 --> 00:00:42,000
My mama always said, life was like a box of chocolates.
'''
    }
]

# Insert sample data into database
for subtitle in sample_subtitles:
    # Create a zip file in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
        zip_file.writestr(f"{subtitle['name']}.srt", subtitle['text'].encode('latin-1'))
    
    # Insert into database
    cursor.execute(
        "INSERT INTO zipfiles (num, name, content) VALUES (?, ?, ?)",
        (subtitle['id'], subtitle['name'], zip_buffer.getvalue())
    )

# Commit changes and close connection
conn.commit()
conn.close()

print(f"Sample database created with {len(sample_subtitles)} subtitle entries in data/eng_subtitles_database.db")
