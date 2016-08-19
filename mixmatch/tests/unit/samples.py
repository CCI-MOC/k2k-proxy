#   Copyright 2016 Massachusetts Open Cloud
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

IMAGE_LIST_V2 = {
    "images": [
        {
            "checksum": "eb9139e4942121f22bbc2afc0400b2a4",
            "container_format": "ami",
            "created_at": "2016-08-19T15:47:10Z",
            "disk_format": "ami",
            "file": "/v2/images/61f655c0-4511-4307-a257-4162c87a5130/file",
            "id": "61f655c0-4511-4307-a257-4162c87a5130",
            "kernel_id": "130b7b71-487a-4553-b336-0a72ec590c99",
            "min_disk": 0,
            "min_ram": 0,
            "name": "cirros-0.3.4-x86_64-uec",
            "owner": "5f4358e168b747a487fe34e64c5619b2",
            "protected": False,
            "ramdisk_id": "941882c5-b992-4fa9-bcba-9d25d2f4e3b8",
            "schema": "/v2/schemas/image",
            "self": "/v2/images/61f655c0-4511-4307-a257-4162c87a5130",
            "size": 25165824,
            "status": "active",
            "tags": [],
            "updated_at": "2016-08-19T15:47:10Z",
            "virtual_size": None,
            "visibility": "public"
        },
        {
            "checksum": "be575a2b939972276ef675752936977f",
            "container_format": "ari",
            "created_at": "2016-08-19T15:47:08Z",
            "disk_format": "ari",
            "file": "/v2/images/941882c5-b992-4fa9-bcba-9d25d2f4e3b8/file",
            "id": "941882c5-b992-4fa9-bcba-9d25d2f4e3b8",
            "min_disk": 0,
            "min_ram": 0,
            "name": "cirros-0.3.4-x86_64-uec-ramdisk",
            "owner": "5f4358e168b747a487fe34e64c5619b2",
            "protected": False,
            "schema": "/v2/schemas/image",
            "self": "/v2/images/941882c5-b992-4fa9-bcba-9d25d2f4e3b8",
            "size": 3740163,
            "status": "active",
            "tags": [],
            "updated_at": "2016-08-19T15:47:08Z",
            "virtual_size": None,
            "visibility": "public"
        },
        {
            "checksum": "8a40c862b5735975d82605c1dd395796",
            "container_format": "aki",
            "created_at": "2016-08-19T15:46:58Z",
            "disk_format": "aki",
            "file": "/v2/images/130b7b71-487a-4553-b336-0a72ec590c99/file",
            "id": "130b7b71-487a-4553-b336-0a72ec590c99",
            "min_disk": 0,
            "min_ram": 0,
            "name": "cirros-0.3.4-x86_64-uec-kernel",
            "owner": "5f4358e168b747a487fe34e64c5619b2",
            "protected": False,
            "schema": "/v2/schemas/image",
            "self": "/v2/images/130b7b71-487a-4553-b336-0a72ec590c99",
            "size": 4979632,
            "status": "active",
            "tags": [],
            "updated_at": "2016-08-19T15:47:02Z",
            "virtual_size": None,
            "visibility": "public"
        }
    ]
}

VOLUME_LIST_V2 = {
    "volumes": [
        {
            "id": "69baebf2-c242-47f4-b0a3-ab1761cfe755",
            "links": [
                {
                    "href": "http://localhost:8776/v2/"
                            "5f4358e168b747a487fe34e64c5619b2/"
                            "volumes/"
                            "69baebf2-c242-47f4-b0a3-ab1761cfe755",
                    "rel": "self"
                },
                {
                    "href": "http://localhost:8776/"
                            "5f4358e168b747a487fe34e64c5619b2/"
                            "volumes/"
                            "69baebf2-c242-47f4-b0a3-ab1761cfe755",
                    "rel": "bookmark"
                }
            ],
            "name": "volume1"
        }
    ]
}
