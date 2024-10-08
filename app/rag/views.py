import logging
import time
import uuid

from .models import Conversation
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.urls import re_path
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_swagger.views import get_swagger_view
from django.shortcuts import get_object_or_404
from .serializers import ChatbotSerializer, FeedbackSerializer, FeedbackStatsSerializer, ConversationSerializer,FeedbackSubmissionSerializer

from .raglogic import get_answer
from .services import (
    clear_conversation,
    get_feedback_stats,
    get_recent_conversations,
    save_conversation,
    save_feedback,
)

# Configure logger
logger = logging.getLogger(__name__)

schema_view = get_swagger_view(title='URA FAQS API')

urlpatterns = [
    re_path(r'^$', schema_view)
]

class ChatView(APIView):
    """
    Main API View for handling user input and returning chatbot responses.
    """
    @swagger_auto_schema(
        request_body=ChatbotSerializer,
        responses={
            200: openapi.Response(
                description="Response from the chatbot",
                examples={
                    "application/json": {
                        "conversation_id": "abcd-1234-efgh-5678",
                        "answer": "This is the chatbot's response.",
                        "relevance": "RELEVANT",
                        "response_time": 0.5,
                        "cost": 0.02,
                        "elapsed_time": 1.0
                    }
                }
            ),
            400: openapi.Response(
                description="Bad Request - Invalid input",
                examples={
                    "application/json": {
                        "error": "Message input is required."
                    }
                }
            ),
            500: openapi.Response(
                description="Internal Server Error",
                examples={
                    "application/json": {
                        "error": "An error occurred while processing your request."
                    }
                }
            ),
        }
    )
    def post(self, request):
        """
        Handles the user's input, sends it to the RAG system, and returns the response.
        """
        serializer = ChatbotSerializer(data=request.data)
        if serializer.is_valid():
            user_input = serializer.validated_data.get("message")
            model_choice = serializer.validated_data.get("model_choice", "openai/gpt-3.5-turbo")
            search_type = serializer.validated_data.get("search_type", "hybrid")

            logger.info(f"Received chatbot request with model: {model_choice} and search type: {search_type}")

            # Generate a conversation ID if not provided
            conversation_id = str(uuid.uuid4())
            request.session["conversation_id"] = conversation_id

            start_time = time.time()

            try:
                logger.info(f"Generating answer for conversation {conversation_id}")
                response = get_answer(user_input, model_choice=model_choice, search_type=search_type)
                logger.info(response)

                answer = response.get("answer", "No answer provided.")
                relevance = response.get("relevance", "N/A")
                response_time = response.get("response_time", "N/A")
                cost = response.get("openai_cost", "N/A")
                elapsed_time = time.time() - start_time

                # Save the conversation
                save_conversation(conversation_id, user_input, response, "URA FAQs")
                logger.info(f"Conversation {conversation_id} saved successfully.")

                return Response({
                    "conversation_id": conversation_id,
                    "answer": answer,
                    "relevance": relevance,
                    "response_time": response_time,
                    "cost": cost,
                    "elapsed_time": elapsed_time
                }, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception(f"Error occurred while processing chatbot request for conversation {conversation_id}: {e}")
                return Response({"error": "An error occurred while processing your request."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClearChatHistoryView(APIView):
    """
    API View to clear the chat history for the current conversation.
    """

    @swagger_auto_schema(
        responses={
            200: "Chat history cleared successfully.",
            400: "No conversation to clear.",
            500: "Internal Server Error",
        }
    )
    def post(self, request):
        conversation_id = request.session.get("conversation_id", None)
        logger.info(f"Attempting to clear chat history for conversation {conversation_id}")

        if conversation_id:
            try:
                clear_conversation(conversation_id)
                request.session["conversation_id"] = str(uuid.uuid4())  # Reset conversation ID
                logger.info(f"Chat history cleared successfully for conversation {conversation_id}.")
                return Response({"message": "Chat history cleared successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception(f"Error occurred while clearing chat history for conversation {conversation_id}: {e}")
                return Response({"error": "An error occurred while clearing the chat history."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        logger.warning("No conversation ID found in the session.")
        return Response({"error": "No conversation to clear."}, status=status.HTTP_400_BAD_REQUEST)

class ConversationDetailView(APIView):
    """
    API View to retrieve a conversation by its ID.
    """

    def get(self, request, id):
        logger.info(f"Fetching conversation with ID: {id}")
        conversation = get_object_or_404(Conversation.objects.prefetch_related('feedback'), id=id)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecentConversationsView(APIView):
    """
    API View to fetch recent conversations.
    """

    @swagger_auto_schema(
        responses={
            200: ConversationSerializer(many=True),
            500: "Internal Server Error",
        }
    )
    def get(self, request):
        relevance_filter = request.query_params.get("relevance", None)
        logger.info(f"Fetching recent conversations with relevance filter: {relevance_filter}")

        try:
            recent_conversations = get_recent_conversations(
                limit=20, relevance=relevance_filter if relevance_filter != "All" else None
                ).prefetch_related('feedback')
            logger.info(f"Successfully fetched recent conversations.")
            serializer = ConversationSerializer(recent_conversations, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error occurred while fetching recent conversations: {e}")
            return Response({"error": "An error occurred while fetching recent conversations."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FeedbackView(APIView):
    """
    API View to save feedback for a specific conversation.
    """

    @swagger_auto_schema(
        request_body=FeedbackSerializer,
        responses={
            200: "Feedback saved successfully.",
            400: "Invalid request data.",
            500: "Failed to save feedback.",
        }
    )
    def post(self, request):
        serializer = FeedbackSubmissionSerializer(data=request.data)

        if serializer.is_valid():
            conversation_id = serializer.validated_data.get("conversation_id")
            feedback = serializer.validated_data.get("feedback")
            
            logger.info(f"Received feedback for conversation {conversation_id}")

            try:
                save_feedback(conversation_id, feedback)
                logger.info(f"Feedback saved successfully for conversation {conversation_id}.")
                return Response({"message": "Feedback saved successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                logger.exception(f"Error occurred while saving feedback for conversation {conversation_id}: {e}")
                return Response({"error": "Failed to save feedback."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FeedbackStatsView(APIView):
    """
    API View to get feedback statistics.
    """

    @swagger_auto_schema(
        responses={
            200: FeedbackStatsSerializer,
            500: "Internal Server Error",
        }
    )
    def get(self, request):
        logger.info("Fetching feedback statistics.")

        try:
            feedback_stats = get_feedback_stats()
            logger.info("Successfully fetched feedback statistics.")
            serializer = FeedbackStatsSerializer(feedback_stats)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.exception(f"Error occurred while fetching feedback statistics: {e}")
            return Response({"error": "An error occurred while fetching feedback statistics."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
