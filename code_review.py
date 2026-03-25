# Senaryo: Dashboard için aktif çekicilerin sayısını ve son logları döner.
def get_dashboard_stats(request):
    # 1. Potansiyel Hata
    all_requests = AssistanceRequest.objects.all()
    total_count = len(all_requests)
    active_providers = []

    # 2. Potansiyel Hata
    providers = Provider.objects.all()
    for p in providers:
        # Son 5 dakikada ping atmış olanlar
        if p.is_active and p.last_ping > datetime.now() - timedelta(minutes=5):
            active_providers.append(p)

    # 3. Hata Potansiyeli
    logs = Log.objects.filter(level='ERROR')[:5]
    log_messages = [l.message for l in logs]
    return {
        "total": total_count,
        "active": len(active_providers),
        "logs": log_messages
    }

# FIXED VERSION

def get_dashboard_stats(request):
    # ✅ 1. Hata: DB'den .all() ile bütün kayıtları getirmek yerine 
    # .count() ile db tarafından istenen sonuç direk alınmalı
    total_count = AssistanceRequest.objects.count()

    # ✅ 2. Hata: DB'den .all() ile bütün kayıtları getirmek yerine
    # istenilen filtreler uygulanıp sonrasında .count() ile sonuca varılmalı
    # öneri: datetime.now() yerine timezone.now() ile bütün projede 
    # aynı noktadan (settings.py) zaman yönetimi yapılmalı
    active_providers_count = Provider.objects.filter(
        is_active=True,
        last_ping__gt=datetime.now() - timedelta(minutes=5),
    ).count()

    # ✅ 3. Hata: Getirilen 5 kayıt için sıra garantisi yok, kayıtları yeniden
    # eskiye sıralayarak kesinlik sağlanmalı (veya alternatif bir order ile)
    # öneri: sadece kullanılacak fieldı almak için values_list kullanılmalı
    logs = Log.objects.filter(level='ERROR').order_by('-created_at').values_list('message', flat=True)[:5]

    return {
        "total": total_count,
        "active": active_providers_count,
        "logs": list(logs)
    }