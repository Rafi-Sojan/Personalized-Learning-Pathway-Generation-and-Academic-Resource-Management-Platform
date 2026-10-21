INSERT INTO courses (id, code, title, description) VALUES
  ('course-python', 'CS101', 'Python Foundations', 'Core programming and problem solving.')
ON CONFLICT (id) DO NOTHING;

INSERT INTO concepts (id, course_id, name, difficulty, status) VALUES
  ('variables', 'course-python', 'Variables and Types', 1, 'completed'),
  ('control-flow', 'course-python', 'Control Flow', 2, 'in_progress'),
  ('functions', 'course-python', 'Functions', 2, 'not_started')
ON CONFLICT (id) DO NOTHING;
