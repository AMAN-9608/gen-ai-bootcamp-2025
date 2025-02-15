from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime
import math

def load(app):
  # todo /study_sessions POST

  @app.route('/api/study-sessions', methods=['GET'])
  @cross_origin()
  def get_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get total count
      cursor.execute('''
        SELECT COUNT(*) as count 
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
      ''')
      total_count = cursor.fetchone()['count']

      # Get paginated sessions
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        GROUP BY ss.id
        ORDER BY ss.created_at DESC
        LIMIT ? OFFSET ?
      ''', (per_page, offset))
      sessions = cursor.fetchall()

      return jsonify({
        'items': [{
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
          'review_items_count': session['review_items_count']
        } for session in sessions],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions', methods=['POST'])
  @cross_origin()
  def create_study_session():
    try:
      data = request.get_json()
      
      # Validate required fields
      required_fields = ['group_id', 'study_activity_id']
      for field in required_fields:
        if field not in data:
          return jsonify({"error": f"Missing required field: {field}"}), 400
      
      group_id = data['group_id']
      study_activity_id = data['study_activity_id']
      
      # Verify group exists
      cursor = app.db.cursor()
      cursor.execute('SELECT id FROM groups WHERE id = ?', (group_id,))
      if not cursor.fetchone():
        return jsonify({"error": "Group not found"}), 404
      
      # Verify study activity exists
      cursor.execute('SELECT id FROM study_activities WHERE id = ?', (study_activity_id,))
      if not cursor.fetchone():
        return jsonify({"error": "Study activity not found"}), 404
      
      # Create new study session
      cursor.execute('''
        INSERT INTO study_sessions (group_id, study_activity_id, created_at)
        VALUES (?, ?, datetime('now'))
      ''', (group_id, study_activity_id))
      
      session_id = cursor.lastrowid
      app.db.commit()
      
      # Fetch the created session
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        WHERE ss.id = ?
      ''', (session_id,))
      
      session = cursor.fetchone()
      
      return jsonify({
        'id': session['id'],
        'group_id': session['group_id'],
        'group_name': session['group_name'],
        'study_activity_id': session['activity_id'],
        'study_activity_name': session['activity_name'],
        'created_at': session['created_at'],
        'start_time': session['created_at'],
        'end_time': session['created_at'],  # Initially same as start_time
        'review_items_count': 0  # New session has no reviews yet
      }), 201
      
    except Exception as e:
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<int:id>', methods=['GET'])
  @cross_origin()
  def get_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Get session details
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      if not session:
        return jsonify({"error": "Study session not found"}), 404

      # Get pagination parameters
      page = request.args.get('page', 1, type=int)
      per_page = request.args.get('per_page', 10, type=int)
      offset = (page - 1) * per_page

      # Get the words reviewed in this session with their review status
      cursor.execute('''
        SELECT 
          w.*,
          COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
          COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
        GROUP BY w.id
        ORDER BY w.kanji
        LIMIT ? OFFSET ?
      ''', (id, per_page, offset))
      
      words = cursor.fetchall()

      # Get total count of words
      cursor.execute('''
        SELECT COUNT(DISTINCT w.id) as count
        FROM words w
        JOIN word_review_items wri ON wri.word_id = w.id
        WHERE wri.study_session_id = ?
      ''', (id,))
      
      total_count = cursor.fetchone()['count']

      return jsonify({
        'session': {
          'id': session['id'],
          'group_id': session['group_id'],
          'group_name': session['group_name'],
          'activity_id': session['activity_id'],
          'activity_name': session['activity_name'],
          'start_time': session['created_at'],
          'end_time': session['created_at'],  # For now, just use the same time
          'review_items_count': session['review_items_count']
        },
        'words': [{
          'id': word['id'],
          'kanji': word['kanji'],
          'romaji': word['romaji'],
          'english': word['english'],
          'correct_count': word['session_correct_count'],
          'wrong_count': word['session_wrong_count']
        } for word in words],
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'total_pages': math.ceil(total_count / per_page)
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<int:id>', methods=['PUT'])
  @cross_origin()
  def update_study_session(id):
    try:
      data = request.get_json()
      cursor = app.db.cursor()
      
      # Verify session exists
      cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (id,))
      if not cursor.fetchone():
        return jsonify({"error": "Study session not found"}), 404
      
      # Build update query dynamically based on provided fields
      update_fields = []
      params = []
      
      if 'group_id' in data:
        # Verify new group exists
        cursor.execute('SELECT id FROM groups WHERE id = ?', (data['group_id'],))
        if not cursor.fetchone():
          return jsonify({"error": "Group not found"}), 404
        update_fields.append('group_id = ?')
        params.append(data['group_id'])
      
      if 'study_activity_id' in data:
        # Verify new activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (data['study_activity_id'],))
        if not cursor.fetchone():
          return jsonify({"error": "Study activity not found"}), 404
        update_fields.append('study_activity_id = ?')
        params.append(data['study_activity_id'])
      
      if 'end_time' in data:
        update_fields.append('end_time = ?')
        params.append(data['end_time'])
      
      if not update_fields:
        return jsonify({"error": "No valid fields to update"}), 400
      
      # Update the session
      params.append(id)
      cursor.execute(f'''
        UPDATE study_sessions 
        SET {', '.join(update_fields)}
        WHERE id = ?
      ''', params)
      
      app.db.commit()
      
      # Fetch updated session
      cursor.execute('''
        SELECT 
          ss.id,
          ss.group_id,
          g.name as group_name,
          sa.id as activity_id,
          sa.name as activity_name,
          ss.created_at,
          ss.end_time,
          COUNT(wri.id) as review_items_count
        FROM study_sessions ss
        JOIN groups g ON g.id = ss.group_id
        JOIN study_activities sa ON sa.id = ss.study_activity_id
        LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
        WHERE ss.id = ?
        GROUP BY ss.id
      ''', (id,))
      
      session = cursor.fetchone()
      
      return jsonify({
        'id': session['id'],
        'group_id': session['group_id'],
        'group_name': session['group_name'],
        'activity_id': session['activity_id'],
        'activity_name': session['activity_name'],
        'start_time': session['created_at'],
        'end_time': session['end_time'] or session['created_at'],
        'review_items_count': session['review_items_count']
      })
      
    except Exception as e:
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<int:id>', methods=['DELETE'])
  @cross_origin()
  def delete_study_session(id):
    try:
      cursor = app.db.cursor()
      
      # Verify session exists
      cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (id,))
      if not cursor.fetchone():
        return jsonify({"error": "Study session not found"}), 404
      
      # Delete associated word review items first (foreign key constraint)
      cursor.execute('DELETE FROM word_review_items WHERE study_session_id = ?', (id,))
      
      # Delete the session
      cursor.execute('DELETE FROM study_sessions WHERE id = ?', (id,))
      
      app.db.commit()
      
      return '', 204
      
    except Exception as e:
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/<int:id>/reviews', methods=['POST'])
  @cross_origin()
  def submit_session_reviews(id):
    try:
      data = request.get_json()
      cursor = app.db.cursor()
      
      # Validate request body
      if not isinstance(data, list):
        return jsonify({"error": "Request body must be an array of reviews"}), 400
      
      # Verify session exists
      cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (id,))
      if not cursor.fetchone():
        return jsonify({"error": "Study session not found"}), 404
      
      # Validate each review item and prepare for insertion
      reviews_to_insert = []
      for review in data:
        if not isinstance(review, dict):
          return jsonify({"error": "Each review must be an object"}), 400
          
        required_fields = ['word_id', 'correct']
        for field in required_fields:
          if field not in review:
            return jsonify({"error": f"Missing required field in review: {field}"}), 400
        
        # Verify word exists
        cursor.execute('SELECT id FROM words WHERE id = ?', (review['word_id'],))
        if not cursor.fetchone():
          return jsonify({"error": f"Word not found: {review['word_id']}"}), 404
        
        # Prepare review for insertion
        reviews_to_insert.append((
          id,  # study_session_id
          review['word_id'],
          1 if review['correct'] else 0,
          review.get('response', None),  # Optional field
          'now'  # created_at
        ))
      
      # Insert all reviews
      cursor.executemany('''
        INSERT INTO word_review_items 
          (study_session_id, word_id, correct, response, created_at)
        VALUES (?, ?, ?, ?, datetime(?))
      ''', reviews_to_insert)
      
      # Update word_reviews materialized view
      cursor.execute('''
        INSERT OR REPLACE INTO word_reviews (word_id, correct_count, wrong_count)
        SELECT 
          word_id,
          SUM(CASE WHEN correct = 1 THEN 1 ELSE 0 END) as correct_count,
          SUM(CASE WHEN correct = 0 THEN 1 ELSE 0 END) as wrong_count
        FROM word_review_items
        GROUP BY word_id
      ''')
      
      app.db.commit()
      
      return jsonify({
        "message": f"Successfully added {len(reviews_to_insert)} reviews",
        "reviews_count": len(reviews_to_insert)
      }), 201
      
    except Exception as e:
      app.db.rollback()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/study-sessions/reset', methods=['POST'])
  @cross_origin()
  def reset_study_sessions():
    try:
      cursor = app.db.cursor()
      
      # First delete all word review items since they have foreign key constraints
      cursor.execute('DELETE FROM word_review_items')
      
      # Then delete all study sessions
      cursor.execute('DELETE FROM study_sessions')
      
      app.db.commit()
      
      return jsonify({"message": "Study history cleared successfully"}), 200
    except Exception as e:
      return jsonify({"error": str(e)}), 500
