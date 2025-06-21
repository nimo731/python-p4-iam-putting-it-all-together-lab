#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from flask_migrate import Migrate

from config import app, db, api
from models import User, Recipe

class Signup(Resource):
    def post(self):
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('username'):
                return {'errors': ['Username is required']}, 422
            if not data.get('password'):
                return {'errors': ['Password is required']}, 422
            
            # Create new user
            user = User(
                username=data['username'],
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            user.password_hash = data['password']
            
            db.session.add(user)
            db.session.commit()
            
            # Save user ID in session
            session['user_id'] = user.id
            
            # Return user data
            return user.to_dict(), 201
            
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422
        except IntegrityError:
            db.session.rollback()
            return {'errors': ['Username already exists']}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if user_id:
            user = User.query.get(user_id)
            if user:
                return user.to_dict(), 200
        
        return {'error': 'Unauthorized'}, 401

class Login(Resource):
    def post(self):
        data = request.get_json()
        
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.authenticate(data['password']):
            session['user_id'] = user.id
            return user.to_dict(), 200
        
        return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        if session.get('user_id'):
            session.pop('user_id', None)
            return {}, 204
        
        return {'error': 'Unauthorized'}, 401

class RecipeIndex(Resource):
    def get(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        
        recipes = Recipe.query.all()
        return [recipe.to_dict() for recipe in recipes], 200
    
    def post(self):
        if not session.get('user_id'):
            return {'error': 'Unauthorized'}, 401
        
        try:
            data = request.get_json()
            
            recipe = Recipe(
                title=data['title'],
                instructions=data['instructions'],
                minutes_to_complete=data['minutes_to_complete'],
                user_id=session['user_id']
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            return recipe.to_dict(), 201
            
        except ValueError as e:
            db.session.rollback()
            return {'errors': [str(e)]}, 422

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')

migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run(port=5555, debug=True)