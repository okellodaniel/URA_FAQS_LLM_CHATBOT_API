import logging
from .models import Conversation, Feedback
from django.utils import timezone
from django.db import DatabaseError

# Logger configuration
logger = logging.getLogger(__name__)

def save_conversation(conversation_id: str, question: str, answer_data: dict, section: str) -> None:
    """
    Save a conversation to the database.
    """
    try:
        logger.info(f"Saving conversation {conversation_id}")
        conversation = Conversation.objects.create(
            id=conversation_id,
            question=question,
            answer=answer_data["answer"],
            section=section,
            model_used=answer_data["model_used"],
            response_time=answer_data["response_time"],
            relevance=answer_data["relevance"],
            relevance_explanation=answer_data["relevance_explanation"],
            prompt_tokens=answer_data["prompt_tokens"],
            completion_tokens=answer_data["completion_tokens"],
            total_tokens=answer_data["total_tokens"],
            eval_prompt_tokens=answer_data["eval_prompt_tokens"],
            eval_completion_tokens=answer_data["eval_completion_tokens"],
            eval_total_tokens=answer_data["eval_total_tokens"],
            openai_cost=answer_data["openai_cost"],
            timestamp=timezone.now(),
        )
        conversation.save()
        logger.info(f"Conversation {conversation_id} saved successfully.")
    except DatabaseError as e:
        logger.error(f"Error saving conversation {conversation_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while saving conversation {conversation_id}: {e}")
        raise


def save_feedback(conversation_id: str, feedback_score: int) -> None:
    """
    Save feedback for a conversation.
    """
    try:
        logger.info(f"Saving feedback for conversation {conversation_id}")
        conversation = Conversation.objects.get(id=conversation_id)
        feedback = Feedback.objects.create(
            conversation=conversation,
            feedback=feedback_score,
            timestamp=timezone.now()
        )
        feedback.save()
        logger.info(f"Feedback for conversation {conversation_id} saved successfully.")
    except Conversation.DoesNotExist:
        logger.error(f"Conversation ID {conversation_id} does not exist.")
        raise ValueError(f"Conversation ID {conversation_id} does not exist.")
    except DatabaseError as e:
        logger.error(f"Error saving feedback for conversation {conversation_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while saving feedback for conversation {conversation_id}: {e}")
        raise


def get_recent_conversations(limit: int = 5, relevance: str = None):
    """
    Retrieve recent conversations from the database.
    """
    try:
        logger.info(f"Fetching recent conversations with relevance: {relevance}")
        if relevance:
            conversations = Conversation.objects.filter(relevance=relevance).order_by('-timestamp')[:limit]
        else:
            conversations = Conversation.objects.all().order_by('-timestamp')[:limit]
        logger.info(f"Fetched {len(conversations)} conversations.")
        return conversations
    except DatabaseError as e:
        logger.error(f"Error fetching recent conversations: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while fetching recent conversations: {e}")
        raise


def get_feedback_stats():
    """
    Get statistics of feedback from the database.
    """
    try:
        logger.info("Fetching feedback stats")
        thumbs_up = Feedback.objects.filter(feedback=1).count()
        thumbs_down = Feedback.objects.filter(feedback=-1).count()
        logger.info(f"Feedback stats fetched: {thumbs_up} thumbs up, {thumbs_down} thumbs down.")
        return {
            "thumbs_up": thumbs_up,
            "thumbs_down": thumbs_down
        }
    except DatabaseError as e:
        logger.error(f"Error fetching feedback stats: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while fetching feedback stats: {e}")
        raise


def clear_conversation(conversation_id: str) -> None:
    """
    Clear a conversation and its associated feedback from the database.
    """
    try:
        logger.info(f"Clearing conversation {conversation_id}")
        conversation = Conversation.objects.get(id=conversation_id)
        conversation.delete()
        logger.info(f"Conversation {conversation_id} cleared successfully.")
    except Conversation.DoesNotExist:
        logger.error(f"Conversation ID {conversation_id} does not exist.")
        raise ValueError(f"Conversation ID {conversation_id} does not exist.")
    except DatabaseError as e:
        logger.error(f"Error clearing conversation {conversation_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while clearing conversation {conversation_id}: {e}")
        raise
