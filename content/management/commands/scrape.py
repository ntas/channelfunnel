from django.core.management.base import BaseCommand
import os
from django.conf import settings
from pprint import pprint
import logging
from content.models import Source, Article

import feedparser
from datetime import datetime

class Command( BaseCommand ):

    def handle( self, *args, **options ):
        for source in Source.objects.filter( scraper = 'feedparser', status__in = ( 'silent', 'live' ) ):
            l = feedparser.parse( source.scraper_config )
            if l[ "bozo" ] == 0 :
                for article in l[ "entries" ]:
                    print "Reading feed entry %s: '%s'" % ( article[ "id" ], article[ "title" ] )
                    a, created = Article.objects.get_or_create(
                        source = source,
                        # Wordpress RSS IDs are unique internet-wide, and are immutable (unlike URLs)
                        source_reference = article[ "id" ],
                        defaults = {
                            'date_created' : datetime.now(),
                            'source_url' : article[ "link" ],
                            'title' : article[ "title" ],
                            'num_comments' : article.get( "slash_comments", 0 ),
                            'summary' : article[ "summary" ],
                            'author' : article.get( "author", "" ),
                            'date_published' : datetime(*(article[ "date_parsed" ][:6])),
                            'status' : "live"
                        }
                    )
                    if created:
                        print "Creating new article."
                    else:
                        print "Updating article."
                    if article.has_key( "content" ):
                        # TODO test for multiple content blocks and pick most appropriate
                        a.body = article[ "content" ][0][ "value" ]
                    a.tags.clear()
                    for tag in article.get( "tags", () ):
                        a.tags.add( tag[ "term" ] )
                    a.save()
            else:
                logging.error( "Could not read feed for file '%s': %s" % ( source.scraper_config, l[ "bozo_exception" ] ) ) 
                logging.error( "Skipping '%s': %s" % ( source.scraper_config, l[ "bozo_exception" ] ) ) 
                break

