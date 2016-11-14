# -*- coding: utf-8 -*-
from collections import Counter
from datetime import datetime
import json
import requests

from django.http import JsonResponse
from django.shortcuts import render, redirect

from djgeojson.serializers import Serializer as GeoJSONSerializer

from .forms import ContributionForm
from .models import Waste, Dustbin, Contribution, Trash, Commune


def contribuer(request):
    """
    Contribute
    View to add a contribution to TrashAdvisor
    """
    if request.method == 'POST':
        form = ContributionForm(request.POST)
        if form.is_valid():
            insee = form.cleaned_data['insee']
            trashes = json.loads(form.cleaned_data['trashes'])
            commune, created = Commune.objects.get_or_create(insee=insee)
            contribution = Contribution(insee=insee, commune=commune, timestamp=datetime.now())
            contribution.save()
            for key, val in trashes.items():
                if len(val) > 0:
                    dustbin = Dustbin.objects.get(id=int(key))
                    for el in val:
                        waste = Waste.objects.get(id=int(el))
                        trash = Trash(contribution=contribution, waste=waste, dustbin=dustbin)
                        trash.save()
            return redirect('resultat', pk=contribution.id)

    return render(request, 'contribuer.html', {
        'form': ContributionForm(),
        'geojson': GeoJSONSerializer().serialize(Commune.objects.all(), geometry_field='geometry', properties=('insee', 'geometry')),
        'wastes': Waste.objects.all(),
        'dustbins': Dustbin.objects.all(),
    })


def resultat(request, pk):
    """
    Result
    View to present the result of a contribution to TrashAdvisor
    """
    contribution = Contribution.objects.get(id=pk)
    contributions = Contribution.objects.all()
    contributeur_num = contributions.filter(insee=contribution.insee).count()
    contributeur_num_nat = contributions.count()
    communes_couvertes = contributions.distinct('insee').count()
    r = requests.get('https://geo.api.gouv.fr/communes?code=%s' % (contribution.insee))

    arrondissements = {
      '75101':"Paris 1er",
      '75102':"Paris 2e",
      '75103':"Paris 3e",
      '75104':"Paris 4e",
      '75105':"Paris 5e",
      '75106':"Paris 6e",
      '75107':"Paris 7e",
      '75108':"Paris 8e",
      '75109':"Paris 9e",
      '75110':"Paris 10e",
      '75111':"Paris 11e",
      '75112':"Paris 12e",
      '75113':"Paris 13e",
      '75114':"Paris 14e",
      '75115':"Paris 15e",
      '75116':"Paris 16e",
      '75117':"Paris 17e",
      '75118':"Paris 18e",
      '75119':"Paris 19e",
      '75120':"Paris 20e",
      '69381':"Lyon 1er",
      '69382':"Lyon 2e",
      '69383':"Lyon 3e",
      '69384':"Lyon 4e",
      '69385':"Lyon 5e",
      '69386':"Lyon 6e",
      '69387':"Lyon 7e",
      '69388':"Lyon 8e",
      '69389':"Lyon 9e",
      '13201':"Marseille 1er",
      '13202':"Marseille 2e",
      '13203':"Marseille 3e",
      '13204':"Marseille 4e",
      '13205':"Marseille 5e",
      '13206':"Marseille 6e",
      '13207':"Marseille 7e",
      '13208':"Marseille 8e",
      '13209':"Marseille 9e",
      '13210':"Marseille 10e",
      '13211':"Marseille 11e",
      '13212':"Marseille 12e",
      '13213':"Marseille 13e",
      '13214':"Marseille 14e",
      '13215':"Marseille 15e",
      '13216':"Marseille 16e"
    }

    if len(r.json()) == 0:
        ville = arrondissements[contribution.insee]
    else:
        ville = r.json()[0]['nom']

    # c'est moche c'est moche c'est moche
    colors = list(Dustbin.objects.all().order_by('order').values_list('name', flat=True))
    colors = [str(b) for b in colors]
    backgroundColor = list(Dustbin.objects.all().order_by('order').values_list('color', flat=True))
    backgroundColor = [str(b) for b in backgroundColor]

    datas = []
    wastes = Waste.objects.all().order_by('order')
    for waste in wastes:
        waste_contribs_commune = Contribution.objects.all().filter(insee=contribution.insee, trash__waste=waste).values_list('trash__dustbin__order', flat=True)
        data = [0] * Dustbin.objects.all().count()
        for key, val in Counter(waste_contribs_commune).items():
            data[key] = val
        datas.append({'labels': colors, 'datasets':[{'data': data, 'backgroundColor': backgroundColor}]})

    return render(request, 'resultat.html', {
        'contributeur_num': contributeur_num,
        'ville': ville,
        'contributeur_num_nat': contributeur_num_nat,
        'communes_couvertes': communes_couvertes,
        'datas': datas,
        'wastes': wastes
    })


def consulter(request):
    return render(request, 'consulter.html', {
        'foo': 'bar',
    })


def contribuer_json(request):
    wastes = Waste.objects.all().order_by('order')
    dustbins = Dustbin.objects.all().order_by('order')
    w = [{'path': waste.image.url, 'name': waste.name} for waste in wastes]
    d = [{'path': dustbin.image.url, 'name': dustbin.name, 'color':dustbin.color} for dustbin in dustbins]
    return JsonResponse({'dechet': w, 'poubelle': d})
