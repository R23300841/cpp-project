FROM public.ecr.aws/lambda/python:3.11

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy your lambda handler
COPY lambda_function.py .

# Set the Lambda handler
CMD ["lambda_function.lambda_handler"]
