"""
Tests for the Subjective Listening Test Forum application.
"""
import os
import json
import unittest
import tempfile
from pathlib import Path

from app import create_app
from utils.loader import scan_audio_directory, randomize_questions, validate_questions
from utils.saver import save, load_results


class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create test audio files
        audio_dir = Path(self.temp_dir.name) / 'audio'
        audio_dir.mkdir()
        
        # Create dummy audio files
        (audio_dir / '001_prompt.mp3').touch()
        (audio_dir / '001_gt.mp3').touch()
        (audio_dir / '001_methodA.mp3').touch()
        (audio_dir / '001_methodB.mp3').touch()
        (audio_dir / '002_prompt.mp3').touch()
        (audio_dir / '002_gt.mp3').touch()
        (audio_dir / '002_methodA.mp3').touch()
        
        # Create results directory
        self.results_dir = Path(self.temp_dir.name) / 'results'
        self.results_dir.mkdir()
    
    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()
    
    def test_scan_audio_directory(self):
        """Test scanning audio directory."""
        audio_dir = Path(self.temp_dir.name) / 'audio'
        audio_models = scan_audio_directory(str(audio_dir))
        
        self.assertIn('001', audio_models)
        self.assertIn('002', audio_models)
        self.assertIn('prompt', audio_models['001'])
        self.assertIn('gt', audio_models['001'])
        self.assertIn('methodA', audio_models['001'])
        self.assertIn('methodB', audio_models['001'])
        self.assertIn('prompt', audio_models['002'])
        self.assertIn('gt', audio_models['002'])
        self.assertIn('methodA', audio_models['002'])
        self.assertNotIn('methodB', audio_models['002'])
    
    def test_randomize_questions(self):
        """Test randomizing questions."""
        questions = [
            {'id': 'q1', 'promptId': '001'},
            {'id': 'q2', 'promptId': '002'},
            {'id': 'q3', 'promptId': '003'}
        ]
        
        # Run randomization multiple times to ensure it's working
        all_same = True
        original_order = [q['id'] for q in questions]
        
        for _ in range(10):
            randomized = randomize_questions(questions)
            randomized_ids = [q['id'] for q in randomized]
            
            # Check that all questions are still present
            self.assertEqual(set(original_order), set(randomized_ids))
            
            # Check if order is different from original
            if randomized_ids != original_order:
                all_same = False
        
        # It's statistically very unlikely to get the same order 10 times
        self.assertFalse(all_same, "Randomization doesn't appear to be working")
    
    def test_validate_questions(self):
        """Test question validation."""
        audio_dir = Path(self.temp_dir.name) / 'audio'
        audio_models = scan_audio_directory(str(audio_dir))
        
        # Valid questions
        valid_questions = [
            {
                'id': 'q1',
                'promptId': '001',
                'models': ['gt', 'methodA', 'methodB']
            }
        ]
        
        errors = validate_questions(valid_questions, audio_models)
        self.assertEqual(len(errors), 0)
        
        # Invalid questions
        invalid_questions = [
            {
                'id': 'q2',
                'promptId': '002',
                'models': ['gt', 'methodA', 'methodB']  # methodB doesn't exist for 002
            },
            {
                'id': 'q3',
                'promptId': '003',  # 003 doesn't exist
                'models': ['gt', 'methodA']
            }
        ]
        
        errors = validate_questions(invalid_questions, audio_models)
        self.assertEqual(len(errors), 2)
    
    def test_save_and_load_results(self):
        """Test saving and loading results."""
        participant = {
            'name': 'Test User',
            'age': '30',
            'gender': 'Male'
        }
        
        answers = {
            'q1': {
                'metrics': {
                    'clarity': 4,
                    'naturalness': 5
                },
                'timeSpent': 45.2
            }
        }
        
        # Save results
        result_file = save(participant, answers, str(self.results_dir))
        
        # Check that file exists
        self.assertTrue(os.path.exists(result_file))
        
        # Load results
        loaded_data = load_results(result_file)
        
        # Check loaded data
        self.assertEqual(loaded_data['participant'], participant)
        self.assertEqual(loaded_data['answers'], answers)
        self.assertIn('timestamp', loaded_data)
        self.assertIn('uuid', loaded_data)


class TestApp(unittest.TestCase):
    """Test Flask application."""
    
    def setUp(self):
        """Set up test environment."""
        self.app = create_app({'TESTING': True})
        self.client = self.app.test_client()
    
    def test_cover_page(self):
        """Test cover page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_participant_page(self):
        """Test participant page."""
        response = self.client.get('/participant/')
        self.assertEqual(response.status_code, 200)
    
    def test_rules_redirect(self):
        """Test rules page redirects without participant info."""
        response = self.client.get('/rules/')
        self.assertEqual(response.status_code, 302)  # Redirect to participant page
    
    def test_questions_redirect(self):
        """Test questions page redirects without participant info."""
        response = self.client.get('/questions/0')
        self.assertEqual(response.status_code, 302)  # Redirect to participant page


if __name__ == '__main__':
    unittest.main()