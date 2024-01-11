from extensions import db

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    transcription = db.Column(db.String)
    file_name = db.Column(db.String, unique=True)

    def __repr__(self):
        return f'{self.id} - {self.title}'
