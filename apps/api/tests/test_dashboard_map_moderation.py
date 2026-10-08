from datetime import timedelta
from uuid import UUID
from sqlalchemy import select
from app.analysis.service import utcnow
from app.models import AdminAudit,Notification,User


def publication(client,headers):
    pet=client.post("/api/v1/pets",headers=headers,json={"name":"Luna","species":"dog","primary_color":"brown","size":"medium","microchip_reference":"PRIVATE-CHIP"}).json()
    case=client.post("/api/v1/lost-cases",headers=headers,json={"pet_id":pet["id"],"lost_at":(utcnow()-timedelta(hours=1)).isoformat(),"latitude":-34.913421,"longitude":-56.173939,"description":"Brown dog","public_location":"Montevideo"}).json()
    return pet,case


def test_owner_dashboard_and_atomic_edit(client,auth_headers):
    pet,case=publication(client,auth_headers)
    assert client.get("/api/v1/me/dashboard").status_code==401
    dashboard=client.get("/api/v1/me/dashboard",headers=auth_headers).json()
    assert dashboard["pets"][0]["id"]==pet["id"]
    assert dashboard["cases"][0]["id"]==case["id"]
    edited=client.patch(f"/api/v1/me/cases/{case['id']}",headers=auth_headers,json={"pet":{"name":"Luna nueva"},"case":{"description":"Updated description","status":"FOUND"}})
    assert edited.status_code==200
    assert not client.get("/api/v1/public/lost-animals").json()["items"]
    other=client.post("/api/v1/auth/register",json={"email":"different@example.test","password":"test-only-passphrase","name":"Other","role":"ADMIN"}).json()
    assert other["user"]["role"]=="USER"
    other_headers={"Authorization":f"Bearer {other['access_token']}"}
    assert client.get("/api/v1/me/dashboard",headers=other_headers).json()["cases"]==[]
    assert client.patch(f"/api/v1/me/cases/{case['id']}",headers=other_headers,json={"pet":{},"case":{}}).status_code==404


def test_public_map_approximates_coordinates_and_filters(client,auth_headers):
    _,case=publication(client,auth_headers)
    obs=client.post("/api/v1/observations",headers=auth_headers,json={"species":"dog","primary_color":"brown","size":"medium","description":"Found dog","source_type":"FOUND_ANIMAL","observed_at":utcnow().isoformat(),"latitude":-34.913421,"longitude":-56.173939}).json()
    data=client.get("/api/v1/public/map").json()
    assert len(data["points"])==2
    assert all(point["latitude"]==-34.91 and point["longitude"]==-56.17 for point in data["points"])
    assert all("owner_id" not in point and "email" not in point and "description" not in point for point in data["points"])
    assert "PRIVATE-CHIP" not in str(data)
    assert client.get("/api/v1/public/map?species=cat").json()["points"]==[]
    assert client.get("/api/v1/public/map?latitude=0&longitude=0&radius_km=5").json()["points"]==[]
    assert client.get("/api/v1/public/map?latitude=0").status_code==422
    assert client.get("/api/v1/public/map?compatible_only=true").status_code==200


def test_moderation_requires_admin_and_hiding_is_reversible(client,auth_headers,db_factory):
    _,case=publication(client,auth_headers)
    report=client.post("/api/v1/reports",json={"target_type":"lost_case","target_id":case["id"],"reason":"SPAM","detail":"Test report"})
    assert report.status_code==201
    rid=report.json()["id"]
    assert client.get("/api/v1/admin/reports",headers=auth_headers).status_code==403
    session=client.get("/api/v1/auth/me",headers=auth_headers).json()
    with db_factory() as db:
        db.get(User,UUID(session["id"])).role="ADMIN";db.commit()
    assert client.get("/api/v1/admin/reports",headers=auth_headers).json()["items"][0]["id"]==rid
    assert client.patch(f"/api/v1/admin/reports/{rid}",headers=auth_headers,json={"action":"HIDE"}).status_code==200
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").status_code==404
    assert not client.get("/api/v1/public/map").json()["points"]
    assert client.patch(f"/api/v1/admin/reports/{rid}",headers=auth_headers,json={"action":"RESTORE"}).status_code==200
    assert client.get(f"/api/v1/public/lost-animals/{case['id']}").status_code==200
    assert client.get("/api/v1/admin/overview",headers=auth_headers).status_code==200
    with db_factory() as db:assert len(list(db.scalars(select(AdminAudit))))==2
    assert client.patch(f"/api/v1/admin/reports/{rid}",headers=auth_headers,json={"action":"BLOCK_AUTHOR"}).status_code==409


def test_admin_correction_preserves_original_and_never_exposes_credentials(client,auth_headers,db_factory):
    _,case=publication(client,auth_headers)
    user=client.get("/api/v1/auth/me",headers=auth_headers).json()
    with db_factory() as db:db.get(User,UUID(user["id"])).role="ADMIN";db.commit()
    result=client.patch(f"/api/v1/admin/publications/lost_case/{case['id']}",headers=auth_headers,json={"description":"Corrected description"})
    assert result.status_code==200
    with db_factory() as db:
        audit=db.scalar(select(AdminAudit));assert audit.details["previous_description"]=="Brown dog"
    data=client.get("/api/v1/admin/records/users",headers=auth_headers).json()
    assert "password_hash" not in str(data) and "email" not in str(data)
