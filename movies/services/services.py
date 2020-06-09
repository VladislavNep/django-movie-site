from django.db.models import Sum, Count
from django.forms import ModelChoiceField
from movies.models import *
from dateutil.relativedelta import relativedelta
import locale
from django.db.models.functions import datetime
from service_objects.services import Service

locale.setlocale(locale.LC_ALL, '')


class GetMovieDetail(Service):
    movie = ModelChoiceField(queryset=Movies.objects.all())

    def process(self):
        movie = self.cleaned_data['movie']

        genres = self._get_genres(movie)
        directors = self._get_directors(movie)
        actors = self._get_actors(movie)
        fees_in_world = self._get_fees_in_world(movie)
        budget = self._get_budget(movie)
        fees_in_usa = self._get_fees_in_usa(movie)
        movie_shot = self._get_movie_shot(movie)
        movie_shots = self._get_movie_shots(movie)

        context = {
            "genres": genres,
            "directors": directors,
            "actors": actors,
            "fees_in_world": fees_in_world,
            "budget": budget,
            "fees_in_usa": fees_in_usa,
            "description": movie.description,
            "movie_shot": movie_shot,
            "movie_shots": movie_shots,
            "title": movie.title,
            "rating_imdb": movie.rating_imdb,
            "rating_kp": movie.rating_kp,
            "world_premiere": movie.world_premiere,
            "rf_premiere": movie.rf_premiere,
            "country": movie.country,
        }

        return context

    def _get_genres(self, movie):
        return ', '.join([q.title for q in movie.categories.filter(parent__title='жанры')])

    def _get_directors(self, movie):
        directors =  ', '.join(
            [f'<a class="text-decoration-none person" href="{q.get_absolute_url()}"><span itemprop="director">'
             f'{q.full_name}</span></a>' for q in movie.directors.all()])

        return directors

    def _get_actors(self, movie):
        actors = ', '.join(
            [f'<a class="text-decoration-none person" href="{q.get_absolute_url()}"><span itemprop="actor">'
             f'{q.full_name}</span></a>' for q in movie.actors.all()])

        return actors

    def _get_fees_in_world(self, movie):
        if movie.fees_in_world:
            fees_in_world = f'{movie.fees_in_world:n}'
        else:
            fees_in_world = movie.fees_in_world

        return fees_in_world

    def _get_budget(self, movie):
        if movie.budget:
            budget = f'{movie.budget:n}'
        else:
            budget = movie.budget

        return budget

    def _get_fees_in_usa(self, movie):
        if movie.fees_in_usa:
            fees_in_usa = f'{movie.fees_in_usa:n}'
        else:
            fees_in_usa = movie.fees_in_usa

        return fees_in_usa

    def _get_movie_shot(self, movie):
        return movie.movieshots_set.last().image.url

    def _get_movie_shots(self, movie):
        return [mov_shot.image.url for mov_shot in movie.movieshots_set.all()]


def get_index_slider_movies(limit=None):
    index_slider_movies = Movies.objects.filter(
        world_premiere__range=(datetime.datetime.today() + relativedelta(months=-4), datetime.datetime.today())) \
        .filter(rating_kp__isnull=False) \
        .order_by('-rating_kp')

    if limit:
        return index_slider_movies[:limit]

    return index_slider_movies


def get_movies_future_premieres(limit=None):
    movie_premieres = Movies.objects.filter(world_premiere__gt=datetime.datetime.now()).order_by('world_premiere')

    if limit:
        return movie_premieres[:limit]

    return movie_premieres


def get_movies_now_in_cinema():
    return Movies.objects.filter(
        rf_premiere__range=(datetime.datetime.today() + relativedelta(months=-1, days=-15),
                            datetime.datetime.today())
    ).filter(categories__title='фильмы')


def get_popular_movies(limit=None):
    popular_movies = Movies.objects.filter(
        world_premiere__range=(datetime.datetime.today() + relativedelta(years=-5),
                               datetime.datetime.today() + relativedelta(months=-2))
    ).filter(
        rating_imdb__gte=5,
        categories__title='фильмы'
    ).order_by(
        '-rating_kp'
    ).exclude(categories__title='мультфильм')

    if limit:
        return popular_movies[:limit]

    return popular_movies


def get_popular_series(limit=None):
    popular_series = Movies.objects.filter(
        world_premiere__range=(datetime.datetime.today() + relativedelta(years=-10),
                               datetime.datetime.today() + relativedelta(months=-2))) \
        .filter(rating_imdb__gte=5) \
        .order_by('-rating_imdb') \
        .filter(categories__title='сериалы')
    if limit:
        return popular_series[:limit]

    return popular_series


def get_new_movies_and_series(limit=None):
    new_movies = Movies.objects.filter(
        world_premiere__range=(datetime.datetime.today() + relativedelta(months=-8),
                               datetime.datetime.today() + relativedelta(months=-2))) \
        .order_by('-world_premiere') \
        .filter(world_premiere__isnull=False) \
        .filter(rating_imdb__gte=5)

    if limit:
        return new_movies[:limit]

    return new_movies


def get_movie_list_by_genre(slug, category_type):
    # category_type is categories slug "movies" or "series"
    return Movies.objects.filter(categories__slug=slug).filter(categories__slug=category_type)


def get_movie_list_by_years(year, category_type):
    # category_type is categories slug "movies" or "series"
    return Movies.objects.filter(world_premiere__year__range=(year[0], year[-1]),
                                 categories__slug=category_type)


def get_movie_list_by_country(country, category_type):
    # category_type is categories slug "movies" or "series"
    return Movies.objects.filter(country__icontains=country,
                                 categories__slug=category_type)


def get_movies_recent_premieres():
    return Movies.objects.filter(
        world_premiere__range=(datetime.datetime.today() + relativedelta(months=-6),
                               datetime.datetime.today())
    ).order_by('-world_premiere')


def get_expected_movies():
    """
    We take all movies with future premieres and sort them by
    descending the number of likes posted by users
    :return: QuerySet
    """
    expected_movies = Movies.objects.filter(world_premiere__gt=datetime.datetime.now()).annotate(
        likes_sum=Sum('likes__value'))
    # if there are no likes, then we output future premieres without sorting
    if expected_movies.exclude(likes_sum=None).exists():
        expected_movies = expected_movies.exclude(likes_sum=None).order_by('-likes_sum')

    return expected_movies


def get_movie_of_month():
    """
    we sort movies by the number of likes and comments left over the past month
    :return: QuerySet
    """
    movie_of_month = Movies.objects.filter(
        likes__liked_on__range=(datetime.datetime.today() + relativedelta(months=-1),
                                datetime.datetime.today()),
        comments__commented_on__range=(datetime.datetime.today() + relativedelta(months=-1),
                                       datetime.datetime.today()),
    ).annotate(
        likes_sum=Sum('likes__value'),
        comments_count=Count('comments__text')
    ).exclude(
        likes_sum=None
    ).order_by('-likes_sum', '-comments_count')

    return movie_of_month


def get_movies_interesting_today():
    """"""


def get_top_movies_russian_classics():
    russian_classics = Movies.objects.filter(
        country__icontains=('СССР' and 'Россия')
    ).exclude(
        rf_premiere__gt=datetime.datetime.today() + relativedelta(months=-3)
    ).exclude(
        rating_kp__isnull=True
    ).order_by('-rating_kp')

    return russian_classics


def get_top_movies_foreign_classics():
    foreign_classics = Movies.objects.exclude(
        country='СССР' and 'Россия',
        world_premiere__gt=datetime.datetime.today() + relativedelta(months=-3),
    ).exclude(
        rating_imdb__isnull=True
    ).order_by('-rating_imdb')

    return foreign_classics


def get_top_movies_by_rating_kp():
    movies_by_rating_kp = Movies.objects.exclude(
        rating_kp__isnull=True
    ).order_by('-rating_kp')

    return movies_by_rating_kp


def get_top_movies_by_rating_imdb():
    movies_by_rating_imdb = Movies.objects.exclude(
        rating_imdb__isnull=True
    ).order_by('-rating_imdb')

    return movies_by_rating_imdb


def get_top_cartoon():
    movies_cartoon = Movies.objects.filter(
        categories__slug='cartoon'
    ).exclude(
        rating_imdb__isnull=True
    ).order_by('-rating_imdb')

    return movies_cartoon
