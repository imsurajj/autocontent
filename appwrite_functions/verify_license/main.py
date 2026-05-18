import os
import re
import json
from datetime import datetime, timezone
try:
    from appwrite.client import Client
    from appwrite.services.databases import Databases
    from appwrite.query import Query
except Exception:
    # Local/editor environment may not have the Appwrite SDK installed.
    # Provide harmless fallbacks so linting/editing doesn't error.
    Client = None
    Databases = None
    class Query:
        @staticmethod
        def equal(_a, _b):
            return None

def main(context):
    """
    AutoContent Pro - Appwrite Serverless Function - verify_license
    Rewritten from scratch for 100% stability.
    """

    # 1. Configuration
    api_key = os.environ.get("APPWRITE_API_KEY")
    project_id = os.environ.get("APPWRITE_FUNCTION_PROJECT_ID")
    endpoint = os.environ.get("APPWRITE_ENDPOINT", "https://sgp.cloud.appwrite.io/v1")
    database_id = os.environ.get("DATABASE_ID", "autocontentdb")
    collection_id = os.environ.get("COLLECTION_ID", "licenses")

    if not api_key or not project_id:
        context.error("Missing API Key or Project ID.")
        return context.res.json({"status": "error", "message": "Server configuration error."}, 500)

    # 2. Init Client
    client = Client()
    client.set_endpoint(endpoint)
    client.set_project(project_id)
    client.set_key(api_key)
    databases = Databases(client)

    # 3. Parse Request
    try:
        if isinstance(context.req.body, str):
            payload = json.loads(context.req.body)
        elif isinstance(context.req.body, dict):
            payload = context.req.body
        else:
            payload = {}
    except Exception as e:
        context.error(f"Payload parse error: {e}")
        return context.res.json({"status": "error", "message": "Invalid payload format."}, 400)

    action = payload.get("action", "verify")
    key = payload.get("key", "").strip()
    hwid = payload.get("hwid", "").strip()

    if not key:
        return context.res.json({"status": "error", "message": "License key is missing."}, 400)

    clean_key = re.sub(r"[\s\-]+", "", key).upper()

    # 4. Fetch the License Document
    try:
        response = databases.list_documents(
            database_id=database_id,
            collection_id=collection_id,
            queries=[Query.equal("licenseKey", clean_key)]
        )
        
        # Safely extract documents array
        if isinstance(response, dict):
            docs = response.get("documents", [])
        else:
            docs = getattr(response, "documents", [])

        if not docs:
            # Fallback 1: Try lowercase search
            try:
                r_low = databases.list_documents(
                    database_id=database_id,
                    collection_id=collection_id,
                    queries=[Query.equal("licenseKey", clean_key.lower())]
                )
                docs = r_low.get("documents", []) if isinstance(r_low, dict) else getattr(r_low, "documents", [])
            except Exception:
                pass

        if not docs:
            # Fallback 2: Try uppercase search
            try:
                r_up = databases.list_documents(
                    database_id=database_id,
                    collection_id=collection_id,
                    queries=[Query.equal("licenseKey", clean_key.upper())]
                )
                docs = r_up.get("documents", []) if isinstance(r_up, dict) else getattr(r_up, "documents", [])
            except Exception:
                pass

        if not docs:
            # Fallback 3: Document ID match
            try:
                single_doc = databases.get_document(database_id, collection_id, clean_key)
                docs = [single_doc]
            except Exception:
                pass
                
        if not docs:
            return context.res.json({"status": "error", "message": "License key not found."}, 404)
            
        raw_doc = docs[0]

    except Exception as e:
        context.error(f"Database error: {e}")
        return context.res.json({"status": "error", "message": "Database error."}, 500)

    # 5. Normalize Document Data
    doc_dict = {}
    try:
        if isinstance(raw_doc, dict):
            doc_dict = raw_doc
        elif hasattr(raw_doc, "to_dict"):
            doc_dict = raw_doc.to_dict()
        else:
            doc_dict = getattr(raw_doc, "__dict__", {})
    except Exception:
        pass

    doc_id = doc_dict.get("$id", getattr(raw_doc, "id", ""))
    if not doc_id and hasattr(raw_doc, "$id"):
        doc_id = getattr(raw_doc, "$id")

    # Handle modern Appwrite SDK nesting dynamic fields in "data" dict
    custom_fields = doc_dict.get("data", doc_dict) if isinstance(doc_dict.get("data"), dict) else doc_dict
    
    def get_field(name, default_val=None):
        val = custom_fields.get(name)
        if val is None:
            val = doc_dict.get(name, default_val)
        return val

    user_name = get_field("userName", None) or get_field("userId", "Active User")
    organization = get_field("organization", "")

    is_active = get_field("isActive", None)
    if is_active is None:
        status = str(get_field("status", "")).strip().lower()
        is_active = (status in ["active", "true", "1"])
    else:
        if isinstance(is_active, bool):
            pass
        elif str(is_active).strip().lower() in ["true", "1", "yes", "active"]:
            is_active = True
        else:
            is_active = False

    expires_at = get_field("expiresAt")
    
    stored_hwid = get_field("hardwareId") or get_field("hwid", "")
    if stored_hwid in [None, "NULL", "null", "None", ""]:
        stored_hwid = ""
    else:
        stored_hwid = str(stored_hwid).strip()

    # 7. Action: DEACTIVATE
    if action == "deactivate":
        if not stored_hwid or stored_hwid == hwid:
            try:
                databases.update_document(
                    database_id=database_id,
                    collection_id=collection_id,
                    document_id=doc_id,
                    data={
                        "isActive": False,
                        "hardwareId": ""
                    }
                )
                return context.res.json({"status": "success", "message": "License deactivated successfully."}, 200)
            except Exception as e:
                context.error(f"Deactivate error: {e}")
                return context.res.json({"status": "error", "message": "Failed to update database."}, 500)
        else:
            return context.res.json({"status": "error", "message": "HWID mismatch. Cannot deactivate."}, 400)

    # 8. Action: VERIFY
    if not is_active:
        return context.res.json({"status": "error", "message": "License is inactive or revoked."}, 403)

    if expires_at:
        try:
            expiry_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expiry_dt.tzinfo is None:
                expiry_dt = expiry_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) > expiry_dt:
                return context.res.json({"status": "error", "message": "License has expired."}, 403)
        except Exception as e:
            context.error(f"Expiry parsing error: {e}")

    # HWID lock logic
    if not stored_hwid:
        try:
            databases.update_document(
                database_id=database_id,
                collection_id=collection_id,
                document_id=doc_id,
                data={
                    "hardwareId": hwid
                }
            )
            stored_hwid = hwid
        except Exception as e:
            context.error(f"Locking HWID failed: {e}")
    elif stored_hwid != hwid:
        return context.res.json({"status": "error", "message": "License is already active on another machine."}, 403)

    return context.res.json({
        "status": "success",
        "user": user_name,
        "organization": organization,
        "message": "License verified successfully."
    }, 200)
