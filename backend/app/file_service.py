import uuid
import os
import pandas as pd
from .config import OUTPUT_DIR

def create_output_file(data: list, output_format: str):

    df = pd.DataFrame(data)
    file_id = str(uuid.uuid4())

    if output_format == "csv":
        filename = f"{file_id}.csv"
        path = os.path.join(OUTPUT_DIR, filename)
        df.to_csv(path, index=False)

    elif output_format == "excel":
        filename = f"{file_id}.xlsx"
        path = os.path.join(OUTPUT_DIR, filename)
        df.to_excel(path, index=False)

    elif output_format == "json":
        filename = f"{file_id}.json"
        path = os.path.join(OUTPUT_DIR, filename)
        df.to_json(path, orient="records", indent=2)

    else:
        return None, None

    return filename, path
