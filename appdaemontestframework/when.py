"""When wrapper module."""


from datetime import datetime


class WhenWrapper:
    """When wrapper class.

    Args:
        given_that (GivenThat): given that wrapper.
    """

    # pylint: disable=too-few-public-methods
    # ^^ architecture was predefined already

    def __init__(self, given_that):
        self._given_that = given_that

    def state_of(self, entity_id):
        """Get state of wrapper.

        Args:
            entity_id (str): entity id to generate the wrapper for.

        Returns:
            IsWrapper: state of wrapper instance.
        """
        mocked_states = self._given_that.mocked_states
        listen_state = self._given_that._hass_mocks.hass_functions[
            "listen_state"
        ]

        class IsWrapper:
            """IsWrapper class."""

            # pylint: disable=too-few-public-methods
            # ^^ architecture was predefined already

            def is_set_to(
                self,
                state: str,
                attributes: dict = None,
                last_updated: datetime = None,
                last_changed: datetime = None,
            ):
                """Set state of entity.

                Args:
                    state (str): state to be set.
                    attributes (dict): attributes of the state. Default: None.
                    last_updated (datetime): last updated. Default: None.
                    last_changed (datetime): last changed. Default: None.
                """
                # Get old state
                old_state = mocked_states[entity_id]["main"]

                # Save new state
                mocked_states[entity_id] = {
                    "main": state,
                    "attributes": attributes or {},
                    "last_updated": last_updated,
                    "last_changed": last_changed,
                }

                # Call callback
                for call in listen_state.call_args_list:
                    if entity_id == call.args[1]:
                        if (
                            not call.kwargs
                            or "duration" in call.kwargs
                            or (
                                "new" in call.kwargs
                                and call.kwargs["new"] == state
                            )
                        ):
                            callback = call.args[0]
                            callback(entity_id, None, old_state, state, None)

        return IsWrapper()
