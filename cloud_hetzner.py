#!/usr/bin/python3

import requests
import json

##############################
# Hetzner Cloud API DNS part #
##############################

BASE_URL = 'https://api.hetzner.cloud/v1/'

class DNSHetzner:

    def __init__(self, authtoken = ''):
        self.authtoken = authtoken

    def _send_request(self, method, url, params={}, data={}):
        headers = { 'Authorization': f"Bearer {self.authtoken}" }
        postdata = None
        if data:
            postdata = json.dumps(data)
            headers['Content-Type'] = 'application/json'
        response = requests.request(method = method,
                                    url = url,
                                    params = params,
                                    headers = headers,
                                    data = postdata,
                                    )
        response.raise_for_status()
        return(json.loads(response.content))

    # We just implement very simple functions which are good enough for 99% of the cases

    def _get_records(self, zoneid):
        resp = self._send_request('GET', BASE_URL+'records', {'zone_id': zoneid})
        if resp and 'records' in resp:
            return(resp['records'])
        else:
            return([])

    # Keep in mind, that RRsets are uniquely identified by name and type but can have several records

    def get_records(self, zone, name, type_):
        try:
            resp = self._send_request('GET', f"{BASE_URL}zones/{zone}/rrsets/{name}/{type_}")
            return [ record['value'] for record in resp['rrset']['records'] ]
        except requests.exceptions.HTTPError as e:
            return []

    def create_record(self, zone, name, type_, value, ttl=None):
        data = {'name': name, 'type': type_, 'records': [ {'value': value} ] }
        if ttl:
            data['ttl'] = ttl
        resp = self._send_request('POST', f"{BASE_URL}zones/{zone}/rrsets", {}, data)
        return [ record['value'] for record in resp['rrset']['records'] ]

    def update_record(self, zone, name, type_, value):
        data = {'records': [ {'value': value} ] }
        resp = self._send_request('POST', f"{BASE_URL}zones/{zone}/rrsets/{name}/{type_}/actions/set_records", {}, data)
        # This just returns an action

    def delete_record(self, zone, name, type_):
        resp = self._send_request('DELETE', BASE_URL+'records/{recid}'.format(recid = recid))
        # This just returns an action

    # more advanced functions

    def find_zone_for_fqdn(self, fqdn):
        parts = fqdn.split('.')
        return '.'.join(parts[-2:]),'.'.join(parts[0:-2])

    def create(self, fqdn, type_, value, ttl=None):
        zonename, recordname = self.find_zone_for_fqdn(fqdn)
        self.create_record(zonename, recordname, type_, value, ttl)
        return({'action': 'created', 'zone': zonename, 'name': recordname, 'type': type_, 'value': value})

    def update(self, fqdn, type_, value, ttl=None, oldvalue=None, createIfMissing=True):
        zonename, recordname = self.find_zone_for_fqdn(fqdn)
        records = self.get_records(zonename, recordname, type_)    # we would not need to read it for update, but we then already known whether to create or update
        if len(records) == 1 and records[0] == value:
            action = 'checked'
        elif len(records) == 0:
            if createIfMissing:
                self.create_record(zonename, recordname, type_, value, ttl)
                action = 'created'
            else:
                action = 'not created'
        else:
            self.update_record(zonename, recordname, type_, value)
            action = 'updated'
        return({'action': action, 'zone': zonename, 'name': recordname, 'type': type_, 'value': value})

    def delete(self, fqdn, type_):
        zonename, recordname = self.find_zone_for_fqdn(fqdn)
        delete_record(zonename, recordname, type_)
        return({'deleted': action, 'zone': zonename, 'name': recordname, 'type': type_})


