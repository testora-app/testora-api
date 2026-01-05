import os
from openai import OpenAI
from globals import OPENAI_API_KEY


class OpenAIIntegration(object):
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"  # Default model

    def ask_question(self, subject, topic, question, curriculum_content=None):
        """
        Generate a response from ChatGPT based on the question and curriculum content
        
        Args:
            subject (str): The academic subject
            topic (str): Specific topic within the subject
            question (str): Student's question
            curriculum_content (str, optional): Relevant curriculum content
            
        Returns:
            dict: Response from OpenAI API
        """
        # Build the system prompt with educational guidance
        system_prompt = (
            "You are an educational assistant helping students understand topics in their curriculum. "
            "Provide clear, concise explanations appropriate for students. "
            "Only answer questions related to educational topics and within the specified subject area."
        )
        
        # Build the user prompt with context
        user_prompt = f"Subject: {subject}\nTopic: {topic}\n"
        if curriculum_content:
            user_prompt += f"\nCurriculum Context:\n{curriculum_content}\n\n"
        
        user_prompt += f"Student Question: {question}\n\nProvide a helpful, educational response."
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=750,
                temperature=0.7
            )
            
            return {
                "status": True,
                "data": {
                    "answer": response.choices[0].message.content
                }
            }
        except Exception as e:
            return {
                "status": False,
                "message": f"Error generating response: {str(e)}"
            }


# Create a singleton instance
openai_integration = OpenAIIntegration(api_key=OPENAI_API_KEY)