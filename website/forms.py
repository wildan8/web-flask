# website/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8)
    ])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    full_name = StringField('Nama Lengkap', validators=[DataRequired()])
    business_name = StringField('Nama Usaha', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('confirm', message='Password harus sama dengan konfirmasi')
    ])
    confirm = PasswordField('Konfirmasi Password', validators=[DataRequired()])
    submit = SubmitField('Register')

class ResetPasswordRequestForm(FlaskForm):
    username_or_email = StringField('Username atau Email', validators=[DataRequired()])
    submit = SubmitField('Reset Password')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password Baru', validators=[
        DataRequired(),
        Length(min=8, message="Password minimal 8 karakter")
    ])
    confirm = PasswordField('Ulangi Password', validators=[
        DataRequired(),
        EqualTo('password', message='Password harus sama')
    ])
    submit = SubmitField('Reset Password')