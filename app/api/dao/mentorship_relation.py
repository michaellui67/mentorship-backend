from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Dict

from app import messages
from app.database.models.mentorship_relation import MentorshipRelationModel
from app.database.models.tasks_list import TasksListModel
from app.database.models.user import UserModel
from app.utils.decorator_utils import email_verification_required
from app.utils.enum_utils import MentorshipRelationState


class MentorshipRelationDAO:

    MAXIMUM_MENTORSHIP_DURATION = timedelta(weeks=24)
    MINIMUM_MENTORSHIP_DURATION = timedelta(weeks=4)

    def create_mentorship_relation(self, user_id: int, data: Dict[str, str]):

        action_user_id = user_id
        mentor_id = data["mentor_id"]
        mentee_id = data["mentee_id"]
        end_date_timestamp = data["end_date"]
        notes = data["notes"]

        is_valid_user_ids = action_user_id == mentor_id or action_user_id == mentee_id
        if not is_valid_user_ids:
            return messages.MATCH_EITHER_MENTOR_OR_MENTEE, HTTPStatus.BAD_REQUEST

        if mentor_id == mentee_id:
            return messages.MENTOR_ID_SAME_AS_MENTEE_ID, HTTPStatus.BAD_REQUEST

        try:
            end_date_datetime = datetime.fromtimestamp(end_date_timestamp)
        except ValueError:
            return messages.INVALID_END_DATE, HTTPStatus.BAD_REQUEST

        now_datetime = datetime.utcnow()
        if end_date_datetime < now_datetime:
            return messages.END_TIME_BEFORE_PRESENT, HTTPStatus.BAD_REQUEST

        max_relation_duration = end_date_datetime - now_datetime
        if max_relation_duration > self.MAXIMUM_MENTORSHIP_DURATION:
            return messages.MENTOR_TIME_GREATER_THAN_MAX_TIME, HTTPStatus.BAD_REQUEST

        if max_relation_duration < self.MINIMUM_MENTORSHIP_DURATION:
            return messages.MENTOR_TIME_LESS_THAN_MIN_TIME, HTTPStatus.BAD_REQUEST

        mentor_user = UserModel.find_by_id(mentor_id)
        if mentor_user is None:
            return messages.MENTOR_DOES_NOT_EXIST, HTTPStatus.NOT_FOUND

        if not mentor_user.available_to_mentor:
            return messages.MENTOR_NOT_AVAILABLE_TO_MENTOR, HTTPStatus.BAD_REQUEST

        mentee_user = UserModel.find_by_id(mentee_id)
        if mentee_user is None:
            return messages.MENTEE_DOES_NOT_EXIST, HTTPStatus.NOT_FOUND

        if not mentee_user.need_mentoring:
            return messages.MENTEE_NOT_AVAIL_TO_BE_MENTORED, HTTPStatus.BAD_REQUEST

        all_mentor_relations = (
            mentor_user.mentor_relations + mentor_user.mentee_relations
        )
        for relation in all_mentor_relations:
            if relation.state == MentorshipRelationState.ACCEPTED:
                return messages.MENTOR_ALREADY_IN_A_RELATION, HTTPStatus.BAD_REQUEST

        all_mentee_relations = (
            mentee_user.mentor_relations + mentee_user.mentee_relations
        )
        for relation in all_mentee_relations:
            if relation.state == MentorshipRelationState.ACCEPTED:
                return messages.MENTEE_ALREADY_IN_A_RELATION, HTTPStatus.BAD_REQUEST

        tasks_list = TasksListModel()
        tasks_list.save_to_db()

        mentorship_relation = MentorshipRelationModel(
            action_user_id=action_user_id,
            mentor_user=mentor_user,
            mentee_user=mentee_user,
            creation_date=datetime.utcnow().timestamp(),
            end_date=end_date_timestamp,
            state=MentorshipRelationState.PENDING,
            notes=notes,
            tasks_list=tasks_list,
        )

        mentorship_relation.save_to_db()

        return messages.MENTORSHIP_RELATION_WAS_SENT_SUCCESSFULLY, HTTPStatus.CREATED

    @staticmethod
    @email_verification_required
    def list_mentorship_relations(user_id=None, state=None):

        valid_states = ["PENDING", "ACCEPTED", "REJECTED", "CANCELLED", "COMPLETED"]

        def isValidState(rel_state):
            if rel_state in valid_states:
                return True
            return False

        user = UserModel.find_by_id(user_id)
        all_relations = user.mentor_relations + user.mentee_relations

        if state:
            if isValidState(state):
                all_relations = list(
                    filter(lambda rel: (rel.state.name == state), all_relations)
                )
            else:
                return [], HTTPStatus.BAD_REQUEST

        for relation in all_relations:
            setattr(relation, "sent_by_me", relation.action_user_id == user_id)

        return all_relations, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def accept_request(user_id: int, request_id: int):

        user = UserModel.find_by_id(user_id)
        request = MentorshipRelationModel.find_by_id(request_id)

        if request is None:
            return (
                messages.MENTORSHIP_RELATION_REQUEST_DOES_NOT_EXIST,
                HTTPStatus.NOT_FOUND,
            )

        if request.state != MentorshipRelationState.PENDING:
            return messages.NOT_PENDING_STATE_RELATION, HTTPStatus.FORBIDDEN

        if request.action_user_id == user_id:
            return messages.CANT_ACCEPT_MENTOR_REQ_SENT_BY_USER, HTTPStatus.FORBIDDEN

        if not (request.mentee_id == user_id or request.mentor_id == user_id):
            return messages.CANT_ACCEPT_UNINVOLVED_MENTOR_RELATION, HTTPStatus.FORBIDDEN

        my_requests = user.mentee_relations + user.mentor_relations

        for my_request in my_requests:
            if my_request.state == MentorshipRelationState.ACCEPTED:
                return (
                    messages.USER_IS_INVOLVED_IN_A_MENTORSHIP_RELATION,
                    HTTPStatus.FORBIDDEN,
                )

        mentee = request.mentee
        mentor = request.mentor

        if user_id == mentor.id:
            mentee_requests = mentee.mentee_relations + mentee.mentor_relations

            for mentee_request in mentee_requests:
                if mentee_request.state == MentorshipRelationState.ACCEPTED:
                    return messages.MENTEE_ALREADY_IN_A_RELATION, HTTPStatus.BAD_REQUEST

        else:
            mentor_requests = mentor.mentee_relations + mentor.mentor_relations

            for mentor_request in mentor_requests:
                if mentor_request.state == MentorshipRelationState.ACCEPTED:
                    return messages.MENTOR_ALREADY_IN_A_RELATION, HTTPStatus.BAD_REQUEST

        request.state = MentorshipRelationState.ACCEPTED
        request.save_to_db()

        return messages.MENTORSHIP_RELATION_WAS_ACCEPTED_SUCCESSFULLY, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def reject_request(user_id: int, request_id: int):

        request = MentorshipRelationModel.find_by_id(request_id)

        if request is None:
            return (
                messages.MENTORSHIP_RELATION_REQUEST_DOES_NOT_EXIST,
                HTTPStatus.NOT_FOUND,
            )

        if request.state != MentorshipRelationState.PENDING:
            return messages.NOT_PENDING_STATE_RELATION, HTTPStatus.FORBIDDEN

        if request.action_user_id == user_id:
            return messages.USER_CANT_REJECT_REQUEST_SENT_BY_USER, HTTPStatus.FORBIDDEN

        if not (request.mentee_id == user_id or request.mentor_id == user_id):
            return (
                messages.CANT_REJECT_UNINVOLVED_RELATION_REQUEST,
                HTTPStatus.FORBIDDEN,
            )

        request.state = MentorshipRelationState.REJECTED
        request.save_to_db()

        return messages.MENTORSHIP_RELATION_WAS_REJECTED_SUCCESSFULLY, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def cancel_relation(user_id: int, relation_id: int):

        request = MentorshipRelationModel.find_by_id(relation_id)

        if request is None:
            return (
                messages.MENTORSHIP_RELATION_REQUEST_DOES_NOT_EXIST,
                HTTPStatus.NOT_FOUND,
            )

        if request.state != MentorshipRelationState.ACCEPTED:
            return messages.UNACCEPTED_STATE_RELATION, HTTPStatus.FORBIDDEN

        if not (request.mentee_id == user_id or request.mentor_id == user_id):
            return messages.CANT_CANCEL_UNINVOLVED_REQUEST, HTTPStatus.FORBIDDEN

        request.state = MentorshipRelationState.CANCELLED
        request.save_to_db()

        return messages.MENTORSHIP_RELATION_WAS_CANCELLED_SUCCESSFULLY, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def delete_request(user_id: int, request_id: int):

        request = MentorshipRelationModel.find_by_id(request_id)

        if request is None:
            return (
                messages.MENTORSHIP_RELATION_REQUEST_DOES_NOT_EXIST,
                HTTPStatus.NOT_FOUND,
            )

        if request.state != MentorshipRelationState.PENDING:
            return messages.NOT_PENDING_STATE_RELATION, HTTPStatus.FORBIDDEN

        if request.action_user_id != user_id:
            return messages.CANT_DELETE_UNINVOLVED_REQUEST, HTTPStatus.FORBIDDEN

        request.delete_from_db()

        return messages.MENTORSHIP_RELATION_WAS_DELETED_SUCCESSFULLY, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def list_past_mentorship_relations(user_id: int):

        user = UserModel.find_by_id(user_id)
        now_timestamp = datetime.utcnow().timestamp()
        past_relations = list(
            filter(
                lambda relation: relation.end_date < now_timestamp,
                user.mentor_relations + user.mentee_relations,
            )
        )

        for relation in past_relations:
            setattr(relation, "sent_by_me", relation.action_user_id == user_id)

        return past_relations, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def list_current_mentorship_relation(user_id: int):

        user = UserModel.find_by_id(user_id)
        all_relations = user.mentor_relations + user.mentee_relations

        for relation in all_relations:
            if relation.state == MentorshipRelationState.ACCEPTED:
                setattr(relation, "sent_by_me", relation.action_user_id == user_id)
                return relation

        return messages.NOT_IN_MENTORED_RELATION_CURRENTLY, HTTPStatus.OK

    @staticmethod
    @email_verification_required
    def list_pending_mentorship_relations(user_id: int):

        user = UserModel.find_by_id(user_id)
        now_timestamp = datetime.utcnow().timestamp()
        pending_requests = []
        all_relations = user.mentor_relations + user.mentee_relations

        for relation in all_relations:
            if (
                relation.state == MentorshipRelationState.PENDING
                and relation.end_date > now_timestamp
            ):
                setattr(relation, "sent_by_me", relation.action_user_id == user_id)
                pending_requests += [relation]

        return pending_requests, HTTPStatus.OK
