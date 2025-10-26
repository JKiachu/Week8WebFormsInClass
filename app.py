from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy  #part of slide 4 powerpoint(week 7)
from datetime import datetime, timezone #part of slide 4 powerpoint(week 7)
import random
import time

app = Flask(__name__)

app.secret_key = 'A3H3Nregret!0131'

#start slide 4 powerpoint from week 7
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guestlist.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db=SQLAlchemy(app)
#end slide 4 powerpoint(week 7)

#start slide 5 powerpoint(week 7)
class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) #Nullable forces field to be filled
    email = db.Column(db.String(100), nullable=False)
    quan = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    rel = db.Column(db.String(50), nullable=False)
    accommodations = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

class Feedback(db.Model):
    id= db.Column(db.Integer, primary_key=True)
    rating= db.Column(db.Integer, nullable=False)
    comment= db.Column(db.Text)
    created_at= db.Column(db.DateTime, default=datetime.now(timezone.utc))

with app.app_context():
    db.create_all()
#end slide 5 powerpoint(week 7)

@app.route('/')
def index():
    return redirect(url_for('profile'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        quan = request.form.get('quan','').strip()
        comments = request.form.get('comments','').strip()
        rel = request.form.get('rel', '').strip()
        accommodations = request.form.get('accommodations') == "yes"    #true if checked

        #Validation
        if not name or not email or not quan or not rel:
            error = "Please fill in all required fields"
            return render_template('profileForm.html', error=error)
        
        #slide 7(week 7 powerpoint) New profile in database
        try:
            new_profile = Profile(
                name=name,
                email=email,
                quan=int(quan),
                comment=comments,
                rel=rel,
                accommodations=accommodations
            )
            db.session.add(new_profile)
            db.session.commit()
        except Exception as e: 
            db.session.rollback()
            error= "An error has occured. Please try again"
            return render_template('profileForm.html', error=error)
        #end slide 7(wk7 pp)

        
        return render_template('profileSuccess.html', name=name, email=email, quan=quan, comments=comments, rel=rel, accommodations=accommodations)

    return render_template('profileForm.html')

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if request.method=="POST":
        rating=request.form.get('rating', '').strip()
        feedback=request.form.get('feedback', '').strip()

        if not rating:
            errorMsg="Please provide a rating"
            return render_template('feedbackform.html', error=errorMsg)
        
        #slide 8(wk7 pp)
        try:
            new_feedback = Feedback(
                rating=int(rating),
                comment=feedback,
            )
            db.session.add(new_feedback)
            db.session.commit()
        except Exception as e: 
            db.session.rollback()
            error= "An error has occured. Please try again"
            return render_template('feedbackForm.html', error=error)
        #end slide 8(wk7 pp)
        
        return render_template('feedbacksuccess.html', rating=rating, feedback=feedback)
    return render_template('feedbackform.html')

@app.route('/admin/feedback')
def admin_feedback():
    feedbacks=Feedback.query.all()
    return render_template('Admin_feedback.html', feedbacks=feedbacks)

@app.route('/admin/feedback/append')
def admin_feedback_append():
    try:
        feedback_to_update=Feedback.query.filter(Feedback.rating <=5).all()

        for feedback in feedback_to_update:
            if feedback.comment:
                if "Rating only - no written feedback" not in feedback.comment and "- For Review" not in feedback.comment:
                    feedback.comment += "- For Review"
            else:
                feedback.comment= "Rating only - no written feedback"

        db.session.commit()

        return redirect(url_for('admin_feedback'))
    except Exception as e:
        db.session.rollback()
        error= f"Error updating feedback: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)

@app.route('/admin/feedback/delete_first')
def admin_feedback_deleteFirst():
    try:
        all_feedback = Feedback.query.order_by(Feedback.id).all()
        if len(all_feedback) < 1:
            error= "No profiles to delete"
            feedbacks= Feedback.query.all()
            return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
        first_feedback=all_feedback[0]

        db.session.delete(first_feedback)
        db.session.commit()
        return redirect(url_for('admin_feedback'))
    except Exception as e:
        db.session.rollback()
        error= f"Error deleting feedback: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)

@app.route('/admin/feedback/delete6orMore')
def admin_feedback_delete6orMore():
    try:
        deleted_count=Feedback.query.filter(Feedback.rating >= 6).delete()

        db.session.commit()

        return redirect(url_for('admin_feedback'))
    except Exception as e:
        db.session.rollback()
        error=f"Error deleting ratings 6 or above: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
    
@app.route('/admin/feedback/deleteWrongOpinions')
def admin_feedback_wrongOpinions():
    try:
        deleted_count=Feedback.query.filter(Feedback.rating <=5).delete()

        db.session.commit()

        return redirect(url_for('admin_feedback'))
    
    except Exception as e:
        db.session.rollback()
        error=f"Error deleting wrong opinions: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
    
@app.route('/admin/feedback/deleteNoComments', methods=['POST'])
def admin_feedback_deleteNoComments():
    try:
        noCommentDel=request.form.get('comment', '').strip()
        if not noCommentDel:
            error="Please enter a comment"
            feedbacks=Feedback.query.all()
            return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
        
        empty_values=["n/a", "N/A", "None", "NONE", "none"]

        feedback_to_del = []
        all_feedback=Feedback.query.all()

        for feedback in all_feedback:
            if (feedback.comment is None or
                feedback.comment.strip()==noCommentDel or
                feedback.comment.strip() in empty_values):
                feedback_to_del.append(feedback)
        if not feedback_to_del:
            error=f"No feedback with comments '{noCommentDel}' or empty values"
            feedbacks=Feedback.query.all()
            return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
        for feedback in feedback_to_del:
            db.session.delete(feedback)

        db.session.commit()
        return redirect(url_for('admin_feedback'))
    except Exception as e: 
        db.session.rollback()
        error=f"Error deleting feedback: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
    
@app.route('/admin/feedback/delAll')
def admin_feedback_delAll():
    try:
        deleted_count=Feedback.query.delete()

        db.session.commit()

        return redirect(url_for('admin_feedback'))
    
    except Exception as e:
        db.session.rollback()
        error=f"Error deleting wrong opinions: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)

@app.route('/admin/feedback/add_sample_data')
def admin_feedback_addSampleData():
    try:
        sample_feedbacks = [
            Feedback(rating=1, comment=None),
            Feedback(rating=1, comment="1 Star"),
            Feedback(rating=2, comment=None),
            Feedback(rating=2, comment="2 Star"),
            Feedback(rating=3, comment=None),
            Feedback(rating=3, comment="3 Star"),
            Feedback(rating=4, comment=None),
            Feedback(rating=4, comment="4 Star"),
            Feedback(rating=5, comment=""),
            Feedback(rating=5, comment="5 Star"),
            Feedback(rating=6, comment=""),
            Feedback(rating=6, comment="6 Star"),
            Feedback(rating=7, comment=""),
            Feedback(rating=7, comment="7 Star"), 
            Feedback(rating=8, comment=""),
            Feedback(rating=8, comment="8 Star"),
            Feedback(rating=9, comment=""),
            Feedback(rating=9, comment="9 Star"),
            Feedback(rating=10, comment=""),
            Feedback(rating=10, comment="10 Star"),
            Feedback(rating=10, comment="Best Event Ever"),
            Feedback(rating=1, comment="n/a"),
            Feedback(rating=1, comment="N/A"),
            Feedback(rating=1, comment="none"),
            Feedback(rating=1, comment="None"),
            Feedback(rating=1, comment="NONE"),
            Feedback(rating=1, comment=""),
        ]
        
        for feedback in sample_feedbacks:
            db.session.add(feedback)
        
        db.session.commit()
        
        return redirect(url_for('admin_feedback'))
        
    except Exception as e:
        db.session.rollback()
        error = f"Error adding sample data: {str(e)}"
        feedbacks = Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)

@app.route('/admin/feedback/deletebutton', methods=['POST'])
def admin_feedbackDeleteButton():
    try:
        feedbackId=request.form.get('feedbackId', type=int)

        feedback_to_delete=Feedback.query.filter_by(id=feedbackId).first()

        if not feedback_to_delete:
            error=f'No feedback with specific ID found'
            feedbacks=Feedback.query.all()
            return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
        
        db.session.delete(feedback_to_delete)

        db.session.commit()

        return redirect(url_for('admin_profiles'))
        
    except Exception as e:
        error=f"Error Deleting Profiles: {str(e)}"
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)

@app.route('/admin/feedback/edit', methods=['GET', 'POST'])
def admin_feedback_edit():
    if request.method == 'POST':
        feedbackId=request.form.get("feedbackId", type=int)

        if not feedbackId:
            error="No Feedback ID provided."
            feedbacks=Feedback.query.all()
            return render_template('admin_feedback', feedbacks=feedbacks, error=error)
        
        feedbackToUpdate=Feedback.query.filter_by(id=feedbackId).first()

        if not feedbackToUpdate:
            error=f"No feedback with id {feedbackId} found."
            feedbacks=Feedback.query.all()
            return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
        
        try:
            feedbackToUpdate.rating= int(request.form.get('rating', feedbackToUpdate.rating))
            feedbackToUpdate.comment= request.form.get('comment', feedbackToUpdate.comment)
            db.session.commit()
            return redirect(url_for('admin_feedback'))
        except Exception as e:
            db.session.rollback()
            error=f"Error writing changes to database: {str(e)}"
            feedbacks=Feedback.query.all()
            return render_template("admin_feedback.html", feedbacks=feedbacks, error=error)
                            
    feedbackId=request.args.get('feedbackId')

    if not feedbackId:
        error="No feedback ID provided."
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
    
    feedbackToEdit=Feedback.query.filter_by(id=feedbackId).first()

    if not feedbackToEdit:
        error=f"No feedback found with id {feedbackId}."
        feedbacks=Feedback.query.all()
        return render_template('admin_feedback.html', feedbacks=feedbacks, error=error)
    
    return render_template('feedbackFormEdit.html', feedback=feedbackToEdit)