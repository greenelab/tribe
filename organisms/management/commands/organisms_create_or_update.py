import logging # Add python logger module to register errors.
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand
from optparse import make_option
from django.template.defaultfilters import slugify
from django.db import IntegrityError # Picks up integrity errors from the database. For more information, see: https://docs.djangoproject.com/en/dev/ref/exceptions/


from organisms.models import Organism

"""
This custom management command serves to add an organism to the database using a standalone script entered in a command line.
The fields it fills out are the fields specified in the Organism model (in the organisms/models.py file), which is the blueprint
for what information the "organism" will contain in the database.
The user should enter a command line script such as:

python manage.py organisms_add_organism --taxonomy_id=9606 --common_name="Human" --scientific_name="Homo sapiens"

This would enter the new organism "Human" into the database.

For more examples on how django uses custom management commands, see:
https://docs.djangoproject.com/en/dev/howto/custom-management-commands/

"""
class Command(BaseCommand):

    option_list = BaseCommand.option_list + ( # This option_list sets up the command-line options so that the user can enter the organism attributes.
        make_option('--taxonomy_id', action = 'store', dest = 'taxonomy_id', help="Organism Taxonomy ID supplied by NCBI"),
        make_option('--common_name', action = 'store', dest = 'common_name', help="Organism common name, e.g. 'Human'"),
        make_option('--scientific_name', action = 'store', dest = 'scientific_name', help="Organism scientific/binomial name, e.g. 'Homo sapiens'"),
    )

    help = 'Adds a new organism into the database. Fields needed are: taxonomy_id, common_name, and scientific_name.'

    def handle(self, *args, **options):  # Called by the Django API to specify how this object will be saved to the database.
        taxonomy_id = options.get('taxonomy_id', None)
        common_name = options.get('common_name', None)
        scientific_name = options.get('scientific_name', None)
        slug = slugify(scientific_name) # A 'slug' is a label for an object in django, which only contains letters, numbers,
        logger.info("Slug generated: %s", slug) # underscores, and hyphens, thus making it URL-usable.  The slugify method
                                        # in django takes any string and converts it to this format.  For more information, see:
                                        # http://stackoverflow.com/questions/427102/what-is-a-slug-in-django

        if taxonomy_id and common_name and scientific_name:
            try: #organism exists, update with passed parameters
                org = Organism.objects.get(taxonomy_id=taxonomy_id)
                org.common_name = common_name
                org.scientific_name = scientific_name
                org.slug = slug
            except Organism.DoesNotExist: #organism didn't exist, make it
                # Construct an organism object (see: organisms/models.py)
                org = Organism(taxonomy_id=taxonomy_id, common_name=common_name, scientific_name=scientific_name, slug=slug)
            org.save()  # Save to database specified in settings.py
        else:
            # Returns an error if the user did not fill out all fields.
            print("Couldn't add " + str(common_name) + ", scientific_name: " + str(scientific_name) + ", with taxonomy_id " + str(taxonomy_id) + " and slug " + str(slug) + ". Check that all fields are filled correctly.")
            logger.error("Couldn't add scientific_name, with taxonomy_id, and slug into the database.  Check that all fields are filled correctly." )
