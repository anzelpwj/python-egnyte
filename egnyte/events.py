from __future__ import unicode_literals

from egnyte import base, exc, resources



class Event(base.Resource):
    """
    Event.

    Example attributes:
    * id - event id
    * timestamp - date of event in iso8061 format
    * action_source - event source like [ WebUI | SyncEngine | Mobile | PublicAPI ]
    * actor - id of user that generate event
    * type - event type. For now we will support [ file_system | note ]
    * action - event action. For now we will support [ create | delete | move | copy | rename ]
    * object_detail - url to pub api that provide detail info about object from event like https://domain.egnyte.com/pubapi/v1/fs/Shared
    * data - additional data specific for event type and action

    Possible fields for 'data' field:
    for 'type'='file' and action create or delete
        'target_id' - entry id of create/deleted file
        'target_path' - path to created/deleted file
    for 'type'='file' and action move/copy/rename
        'source_path' - source path to moved/copied/renamed file
        'target_path' - target path to moved/copied/renamed file
        'source_id' - source entry id of moved/copied/renamed file (for move/rename there is one entry id so could be only one field or same data for source_id and target_id)
        'target_id' - target entry id of moved/copied/renamed file
    for 'type'='folder' and action create or delete
        'target_path' - path to created/deleted folder
        'folder_id' - folder id of created/deleted folder
    for 'type'='folder' and action move/copy/rename
        'source_path' - source path to moved/copied/renamed folder
        'target_path' - target path to moved/copied/renamed folder
        'source_id' - source folder id of moved/copied/renamed folder
        'target_id' - target folder id of moved/copied/renamed folder
    for 'type'='note' and any available action (create, delete)
        'note_id' - id of added/deleted note

    """
    _url_template = "pubapi/v1/events/%(id)s"

    def user(self):
        """Get a user object based on actor attributes"""
        return resources.User(self._client, id=self.actor)


class Events(base.Resource):
    """
    Events.
    Attributes:

    * latest_event_id - id of latest event
    * oldest_event_id - id of oldest available event
    * timestamp - iso8601 timestamp of latest event
    """
    _url_template = "pubapi/v1/events/cursor"
    _url_template_list = "pubapi/v1/events"
    _lazy_attributes = {'latest_event_id', 'oldest_event_id', 'timestamp'}
    start_id = None
    suppress = None
    folder = None
    types = None
    callbacks = None

    def filter(self, start_id=None, suppress=None, folder=None, types=None):
        """
        Returns a filtered view of the events,

        Parameters:
        * start_id - return all events occurred after id from the previous request (the events shouldn't overlap between calls). defaults to latest_event_id
        * folder (optional) - return events occurred only for this folders and all its content (subfolders, files and notes).
        * suppress (optional) - filter out events from requesting client or filter out events from requesting client done by requesting user. Allowed values: app, user or none (defaults to no filter)
        * types (optional) - return only events of given types.

        """
        if types is not None:
            types = '|'.join(types)
        d = self.__dict__.copy()
        d.update(base.filter_none_values(dict(start_id=start_id, suppress=suppress, type=types)))
        return self.__class__(**d)

    def list(self, start_id, count=None):
        """
        Get detailed data about up to 'count' events 'start_id'.
        """
        if start_id is None:
            start_id = self.start_id
        params = base.filter_none_values(dict(id=start_id, suppress=self.suppress, type=self.types, count=count))
        url = self._client.get_url(self._url_template_list)
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((Event(self._client, **d) for d in json.get('events', ())), json['latest_id'], start_id)

    def poll(self, count=None):
        """
        List events starting with latest_event_id, if any found, update start_id and return them.
        """
        if self.start_id is None:
            self.start_id = self.latest_event_id
        results = self.list(self.start_id, count)
        if results:
            last = results[-1]
            self.start_id = last.id
            self.timestamp = last.timestamp
            self._do_callbacks(results)
        return results

    def _do_callbacks(self, results):
        pass

    def start_polling(self):
        pass




