from django.shortcuts import render


def get_index_page(requesst):

    context = {
        'name': 'CAT',
    }
    return render(requesst, 'index.html', context=context)