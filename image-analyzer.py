import pip
pip.main(["install", "tf_keras"]) # https://github.com/serengil/deepface/issues/1121#issuecomment-2004264510 workaround for missing tf_keras issue from the latest tensorflow (> 2.16)

from flask import Flask, request, jsonify
from deepface import DeepFace
import boto3
import json
from uuid import uuid4
import tempfile
import os
import logging

# Set up logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
s3 = boto3.client('s3')

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Pong"})

@app.route('/invocations', methods=['POST'])
def get_embeddings():
    try:
        data = request.json  # This should auto-parse the JSON request payload
        s3_bucket = data['bucket']
        s3_key = data['key']

        # Generate a secure random filename instead of using the S3 key directly
        secure_filename = str(uuid4())
        temp_dir = tempfile.gettempdir()
        file_path = os.path.normpath(os.path.join(temp_dir, secure_filename))
        if not file_path.startswith(temp_dir):
            raise Exception("Invalid file path: Potential directory traversal detected.")
        
        # Download from S3 using the original key but store with the secure filename
        s3.download_file(s3_bucket, s3_key, file_path)

        print(f'analysing: {file_path}')
        result = DeepFace.represent(
                img_path = file_path,
                model_name = "Facenet512",
                enforce_detection = True,
                detector_backend="retinaface"
            )
        
        # Delete the temp file using the secure path
        os.remove(file_path)

        return json.dumps(result)
    
    except Exception as e:
        # Log the full error details on the server
        error_message = str(e)
        error_type = type(e).__name__
        logger.error(f"Error processing image: {error_message}", exc_info=True)
        
        # Return the actual error details to the client
        error_response = {
            "error_type": error_type,
            "error_message": error_message,
            "error_details": f"Failed to process image from {s3_bucket}/{s3_key}"
        }
        return json.dumps(error_response), 500
    
@app.route('/test', methods=['GET'])
def get_local_image_embeddings():
    try:
        # Path to the local image within the Docker container
        local_image_path = '/tmp/trudeau-3ppl.jpg'

        print(f'Analyzing local image: {local_image_path}')
        result = DeepFace.represent(
            img_path=local_image_path,
            model_name="Facenet512",
            enforce_detection=True,
            detector_backend="retinaface"
        )

        return jsonify(result)

    except Exception as e:
        # Log the full error details on the server
        logger.error(f"Error processing local image: {str(e)}", exc_info=True)
        # Return a generic error message to the client
        return jsonify({"error": "An error occurred while processing the image"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
