#!/usr/bin/env python3

import connexion

if __name__ == '__main__':
    app = connexion.App(__name__, specification_dir='./swagger/')
    app.add_api('swagger.yaml', arguments={'title': '#### Fruitpile REST API\nThe Fruitpile tool allows interaction through a REST API (and is really the normal expected usage mechanism) \n'})
    app.run(port=8088)
