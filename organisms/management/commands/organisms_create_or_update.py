"""
This custom management command serves to add an organism to the database using
a standalone script entered in a command line.  The fields it fills out are the
fields specified in the Organism model (see organisms/models.py), which is the
blueprint for what information the "organism" will contain in the database.
The user should enter a command line script such as:

  python manage.py organisms_create_or_update --taxonomy_id=9606 \
--common_name="Human" --scientific_name="Homo sapiens"

which will enter the new organism "Human" into the database.

For more examples on how django uses custom management commands, see:
https://docs.djangoproject.com/en/dev/howto/custom-management-commands/
"""

import logging
from django.core.management.base import BaseCommand
from optparse import make_option
from django.template.defaultfilters import slugify
from organisms.models import Organism

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Command(BaseCommand):
    # "option_list" sets up the command-line options so that the user can enter
    # the organism attributes.
    option_list = BaseCommand.option_list + (
        make_option(
            '--taxonomy_id', action='store', dest='taxonomy_id',
            help="Organism Taxonomy ID supplied by NCBI"),
        make_option(
            '--common_name', action='store', dest='common_name',
            help="Organism common name, e.g. 'Human'"),
        make_option(
            '--scientific_name', action='store', dest='scientific_name',
            help="Organism scientific/binomial name, e.g. 'Homo sapiens'"),
    )

    help = 'Adds a new organism into the database. Fields needed are: '\
           'taxonomy_id, common_name, and scientific_name.'

    def handle(self, *args, **options):
        """
        This function is called by the Django API to specify how this object
        will be saved to the database.
        """
        taxonomy_id = options.get('taxonomy_id', None)
        common_name = options.get('common_name', None)
        scientific_name = options.get('scientific_name', None)

        # A 'slug' is a label for an object in django, which only contains
        # letters, numbers, underscores, and hyphens, thus making it URL-
        # usable.  The slugify method in django takes any string and converts
        # it to this format.  For more information, see:
        # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django
        slug = slugify(scientific_name)
        logger.info("Slug generated: %s", slug)

        if taxonomy_id and common_name and scientific_name:
            # If organism exists, update with passed parameters
            try:
                org = Organism.objects.get(taxonomy_id=taxonomy_id)
                org.common_name = common_name
                org.scientific_name = scientific_name
                org.slug = slug
            # If organism doesn't exist, construct an organism object
            # (see organisms/models.py).
            except Organism.DoesNotExist:
                org = Organism(taxonomy_id=taxonomy_id,
                               common_name=common_name,
                               scientific_name=scientific_name, slug=slug)
            org.save()  # Save to the database.
        else:
            # Returns an error if the user did not fill out all fields.
            print("Couldn't add " + str(common_name) + ", scientific_name: " +
                  str(scientific_name) + ", with taxonomy_id " +
                  str(taxonomy_id) + " and slug " + str(slug) +
                  ". Check that all fields are filled correctly.")
            logger.error("Couldn't add scientific_name, with taxonomy_id, and "
                         "slug into the database. Check that all fields are "
                         "filled correctly.")
