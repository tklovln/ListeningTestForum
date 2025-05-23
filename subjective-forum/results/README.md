# Results Directory

This directory stores the results of participant listening tests.

## File Format

Results are saved as JSON files with the following naming convention:
`{timestamp}_{uuid}.json`

For example:
`1684932145_a1b2c3d4e5f6g7h8i9j0.json`

## File Structure

Each result file contains:

```json
{
  "participant": {
    "name": "Participant Name",
    "age": "30",
    "gender": "Female",
    "musical_exp": "Advanced",
    "headphones": "Sony WH-1000XM4"
  },
  "answers": {
    "q1": {
      "metrics": {
        "Consistency": 4,
        "Richness": 3,
        "Clarity": 5,
        "Overall Quality": 4
      },
      "timeSpent": 45.2
    },
    "q2": {
      "metrics": {
        "Naturalness": 5,
        "Clarity": 4,
        "Timbre": 3,
        "Overall Quality": 4
      },
      "timeSpent": 38.7
    }
  },
  "timestamp": 1684932145,
  "uuid": "a1b2c3d4e5f6g7h8i9j0"
}
```

## Data Processing

You can process these files using any JSON-compatible tool or library. For example, in Python:

```python
import json
import glob
import pandas as pd

# Load all result files
results = []
for file_path in glob.glob('results/*.json'):
    with open(file_path, 'r') as f:
        results.append(json.load(f))

# Convert to pandas DataFrame for analysis
# (Example for extracting overall quality ratings)
data = []
for result in results:
    participant = result['participant']
    for question_id, answer in result['answers'].items():
        if 'metrics' in answer and 'Overall Quality' in answer['metrics']:
            data.append({
                'participant_name': participant.get('name', 'Unknown'),
                'musical_experience': participant.get('musical_exp', 'Unknown'),
                'question_id': question_id,
                'overall_quality': answer['metrics']['Overall Quality'],
                'time_spent': answer.get('timeSpent', 0)
            })

df = pd.DataFrame(data)
print(df.groupby('question_id')['overall_quality'].mean())
```

## Backup

It's recommended to regularly back up this directory to prevent data loss.