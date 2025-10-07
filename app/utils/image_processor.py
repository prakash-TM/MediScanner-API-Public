import os
import base64
import json
from typing import List, Dict, Any
from openai import OpenAI  # Keep synchronous OpenAI
from app.models.medical import PrescriptionData, Medicine

class PrescriptionImageProcessor:

    def __init__(self):
        self.model = os.getenv("AI_MODEL")
        api_key = os.getenv("AI_API_KEY")
        base_url = os.getenv("AI_API_BASE")
        
        print(f"Using model: {self.model}")
        print(f"api_key: {api_key}")
        print(f"base_url: {base_url}")

        try:
            # Use synchronous OpenAI client
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        except TypeError:
            try:
                self.client = OpenAI(**{"api_key": api_key, "base_url": base_url})
            except TypeError:
                try:
                    import openai as _openai
                    _openai.api_key = api_key
                    _openai.base_url = base_url
                    self.client = OpenAI()
                except Exception:
                    raise

        if not api_key:
            print("Warning: AI_API_KEY not set. API calls will fail without a key.")
        if not self.model:
            print("Warning: model is not configured via AI_MODEL. Using default.")

    def encode_image_to_base64(self, image_bytes: bytes) -> str:
        return base64.b64encode(image_bytes).decode('utf-8')

    def create_extraction_prompt(self) -> str:
        return """You are a highly accurate medical prescription data extraction AI. Your task is to extract structured information from medical prescription images with EXTREME PRECISION and ACCURACY.

CRITICAL REQUIREMENTS:
1. Extract data EXACTLY as written - do not interpret, guess, or modify
2. Medical accuracy is PARAMOUNT - lives depend on correct information
3. If ANY field is unclear, illegible, or not present, use null
4. Double-check all medicine names, dosages, and instructions
5. Verify all numerical values (age, weight, height, temperature)
6. Pay special attention to medicine quantities and timing

FIELDS TO EXTRACT:
- patientName: Patient's full name (string or null)
- age: Patient's age in years (integer or null)
- weight: Patient's weight in kg (float or null)
- height: Patient's height in cm (float or null)
- temperature: Patient's temperature in °F or °C (float or null)
- doctorName: Doctor's full name (string or null)
- hospitalName: Hospital/Clinic name (string or null)
- date: Prescription date in format "YYYY-MM-DD" or as written (string or null)
- medicines: Array of medicine objects, each containing:
  - name: Medicine name EXACTLY as written (string or null)
  - quantity: Number of tablets/doses (integer or null)
  - timeOfIntake: When to take (e.g., "Morning", "Morning-Evening", "3 times daily") (string or null)
  - beforeOrAfterMeals: "Before Meals", "After Meals", or specific instruction (string or null)

RESPONSE FORMAT:
Return ONLY valid JSON with this exact structure:
{
  "patientName": "string or null",
  "age": integer or null,
  "weight": float or null,
  "height": float or null,
  "temperature": float or null,
  "hospitalName": "string or null",
  "doctorName": "string or null",
  "date": "string or null",
  "medicines": [
    {
      "name": "string or null",
      "quantity": integer or null,
      "timeOfIntake": "string or null",
      "beforeOrAfterMeals": "string or null"
    }
  ]
}

IMPORTANT:
- Do NOT include markdown formatting or code blocks
- Return ONLY the raw JSON object
- If the image is not a medical prescription, return all fields as null
- If you cannot read text clearly, use null rather than guessing
"""

    # REMOVED async - now synchronous
    def extract_from_image(self, image_bytes: bytes, image_filename: str) -> PrescriptionData:
        try:
            base64_image = self.encode_image_to_base64(image_bytes)

            file_extension = image_filename.lower().split('.')[-1]
            mime_type_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp'
            }
            mime_type = mime_type_map.get(file_extension, 'image/jpeg')

            # Synchronous call - no await needed
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.create_extraction_prompt()
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )

            # Extract content from response
            try:
                choice = None
                if hasattr(response, "choices") and len(response.choices) > 0:
                    choice = response.choices[0]
                elif isinstance(response, dict) and response.get("choices"):
                    choice = response.get("choices")[0]

                content = None
                if choice is None:
                    content = None
                else:
                    if hasattr(choice, "message") and hasattr(choice.message, "content"):
                        content = choice.message.content
                    elif isinstance(choice, dict):
                        content = None
                        msg = choice.get("message") or {}
                        if isinstance(msg, dict) and msg.get("content") is not None:
                            content = msg.get("content")
                        else:
                            content = choice.get("text") or choice.get("content")

                extracted_text = ""
                if isinstance(content, str):
                    extracted_text = content.strip()
                elif isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, str):
                            parts.append(part)
                        elif isinstance(part, dict):
                            parts.append(str(part.get("text") or part.get("value") or part.get("content") or ""))
                    extracted_text = "\n".join([p for p in parts if p]).strip()
                elif isinstance(content, dict):
                    extracted_text = (content.get("text") or content.get("value") or content.get("content") or "")
                    if isinstance(extracted_text, str):
                        extracted_text = extracted_text.strip()
                    else:
                        extracted_text = str(extracted_text)
                else:
                    extracted_text = ""

                if not extracted_text:
                    try:
                        print("Debug: full response object:\n", repr(response))
                    except Exception:
                        print("Debug: could not repr response object")

            except Exception as e:
                print("Unable to extract text from response object:", e)
                try:
                    print("Full response repr:", repr(response))
                except Exception:
                    pass
                extracted_text = ""

            # Clean up markdown formatting
            if extracted_text.startswith('```json'):
                extracted_text = extracted_text[7:]
            if extracted_text.startswith('```'):
                extracted_text = extracted_text[3:]
            if extracted_text.endswith('```'):
                extracted_text = extracted_text[:-3]
            extracted_text = extracted_text.strip()

            extracted_data = json.loads(extracted_text)

            medicines = []
            for idx, med in enumerate(extracted_data.get("medicines", [])):
                medicine = Medicine(
                    id=f"med_{idx + 1}",
                    name=med.get("name"),
                    quantity=med.get("quantity"),
                    timeOfIntake=med.get("timeOfIntake"),
                    beforeOrAfterMeals=med.get("beforeOrAfterMeals")
                )
                medicines.append(medicine)

            prescription = PrescriptionData(
                patientName=extracted_data.get("patientName"),
                age=extracted_data.get("age"),
                weight=extracted_data.get("weight"),
                height=extracted_data.get("height"),
                temperature=extracted_data.get("temperature"),
                hospitalName=extracted_data.get("hospitalName"),
                doctorName=extracted_data.get("doctorName"),
                date=extracted_data.get("date"),
                medicines=medicines,
                reportImages=[image_filename]
            )

            return prescription

        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {extracted_text}")
            return self._create_empty_prescription(image_filename)
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            import traceback
            traceback.print_exc()
            return self._create_empty_prescription(image_filename)

    def _create_empty_prescription(self, image_filename: str) -> PrescriptionData:
        return PrescriptionData(
            patientName=None,
            age=None,
            weight=None,
            height=None,
            temperature=None,
            hospitalName=None,
            doctorName=None,
            date=None,
            medicines=[],
            reportImages=[image_filename]
        )

    # REMOVED async - now synchronous
    def process_multiple_images(self, images: List[tuple]) -> List[PrescriptionData]:
        results = []
        for idx, (image_bytes, filename) in enumerate(images):
            prescription = self.extract_from_image(image_bytes, filename)
            prescription.serialNo = idx
            results.append(prescription)
        return results