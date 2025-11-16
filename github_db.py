import requests
import json
import base64
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GitHubDB:
    def __init__(self, token, repo, branch="main"):
        self.token = token
        self.repo = repo
        self.branch = branch
        self.base_url = f"https://api.github.com/repos/{repo}/contents"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
    
    def get_file_sha(self, file_path):
        """الحصول على SHA الملف"""
        try:
            url = f"{self.base_url}/{file_path}?ref={self.branch}"
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()["sha"]
            return None
        except Exception as e:
            logger.error(f"خطأ في الحصول على SHA: {e}")
            return None
    
    def read_data(self, file_path="data/users.json"):
        """قراءة البيانات من GitHub"""
        try:
            url = f"{self.base_url}/{file_path}?ref={self.branch}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                content = response.json()["content"]
                # إزالة أي مسافات من المحتوى المشفر
                content_clean = content.replace('\n', '')
                decoded_content = base64.b64decode(content_clean).decode('utf-8')
                return json.loads(decoded_content)
            else:
                # إذا الملف مش موجود، نرجع بيانات فارغة
                logger.info("الملف غير موجود، إنشاء بيانات جديدة")
                return {"pending_requests": [], "approved_members": []}
                
        except Exception as e:
            logger.error(f"خطأ في قراءة البيانات: {e}")
            return {"pending_requests": [], "approved_members": []}
    
    def save_data(self, data, file_path="data/users.json"):
        """حفظ البيانات على GitHub"""
        try:
            # تحويل البيانات إلى JSON
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            encoded_data = base64.b64encode(json_data.encode('utf-8')).decode('utf-8')
            
            # الحصول على SHA الملف إذا موجود
            file_sha = self.get_file_sha(file_path)
            
            # إعداد البيانات للإرسال
            payload = {
                "message": f"🤖 تحديث تلقائي - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "content": encoded_data,
                "branch": self.branch
            }
            
            if file_sha:
                payload["sha"] = file_sha
            
            url = f"{self.base_url}/{file_path}"
            response = requests.put(url, headers=self.headers, json=payload)
            
            if response.status_code in [200, 201]:
                logger.info("✅ تم حفظ البيانات على GitHub بنجاح")
                return True
            else:
                logger.error(f"❌ فشل في حفظ البيانات: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ البيانات: {e}")
            return False
    
    def save_pending_request(self, user_data):
        """حفظ طلب جديد"""
        try:
            data = self.read_data()
            
            # منع التكرار
            for user in data["pending_requests"]:
                if user.get("telegram_id") == user_data["telegram_id"]:
                    logger.info("المستخدم لديه طلب معلق مسبقاً")
                    return True
            
            data["pending_requests"].append(user_data)
            success = self.save_data(data)
            
            if success:
                logger.info(f"✅ تم حفظ طلب المستخدم {user_data['username']}")
            return success
            
        except Exception as e:
            logger.error(f"خطأ في حفظ الطلب: {e}")
            return False
    
    def get_pending_requests(self):
        """جلب الطلبات المعلقة"""
        data = self.read_data()
        return data.get("pending_requests", [])
    
    def get_approved_members(self):
        """جلب الأعضاء المعتمدين"""
        data = self.read_data()
        return data.get("approved_members", [])
    
    def approve_member(self, telegram_id):
        """نقل عضو من المعلقة إلى المعتمدة"""
        try:
            data = self.read_data()
            
            # البحث عن المستخدم في الطلبات المعلقة
            user_index = -1
            user_data = None
            
            for i, user in enumerate(data["pending_requests"]):
                if user.get("telegram_id") == telegram_id:
                    user_index = i
                    user_data = user
                    break
            
            if user_data and user_index != -1:
                # نقل إلى الأعضاء المعتمدين
                user_data["approved_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                user_data["approved_by"] = "admin"
                
                data["approved_members"].append(user_data)
                
                # حذف من الطلبات المعلقة
                data["pending_requests"].pop(user_index)
                
                success = self.save_data(data)
                if success:
                    logger.info(f"✅ تم اعتماد المستخدم {user_data.get('username')}")
                return success
            
            return False
        except Exception as e:
            logger.error(f"خطأ في اعتماد العضو: {e}")
            return False
    
    def reject_member(self, telegram_id):
        """رفض عضو"""
        try:
            data = self.read_data()
            original_count = len(data["pending_requests"])
            
            data["pending_requests"] = [
                user for user in data["pending_requests"] 
                if user.get("telegram_id") != telegram_id
            ]
            
            if len(data["pending_requests"]) < original_count:
                success = self.save_data(data)
                if success:
                    logger.info(f"✅ تم رفض المستخدم {telegram_id}")
                return success
            return False
        except Exception as e:
            logger.error(f"خطأ في رفض العضو: {e}")
            return False
    
    def is_user_pending(self, telegram_id):
        """التحقق إذا كان المستخدم لديه طلب معلق"""
        data = self.read_data()
        for user in data.get("pending_requests", []):
            if user.get("telegram_id") == telegram_id:
                return True
        return False
    
    def is_user_approved(self, telegram_id):
        """التحقق إذا كان المستخدم معتمد"""
        data = self.read_data()
        for user in data.get("approved_members", []):
            if user.get("telegram_id") == telegram_id:
                return True
        return False
    
    def get_stats(self):
        """الحصول على إحصائيات"""
        data = self.read_data()
        return {
            "pending": len(data.get("pending_requests", [])),
            "approved": len(data.get("approved_members", [])),
            "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
