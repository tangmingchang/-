#!/usr/bin/env python3
"""
修复用户密码脚本
"""
import sys
from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash, verify_password

def main():
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("开始诊断和修复用户...")
        print("=" * 60)
        
        users_to_fix = [
            ("student1", "学生1", "student"),
            ("teacher1", "教师1", "teacher")
        ]
        
        for username, full_name, role in users_to_fix:
            print(f"\n处理用户: {username}")
            print("-" * 60)
            
            user = db.query(User).filter(User.username == username).first()
            
            if user:
                print(f"  ✅ 用户存在 (ID: {user.id})")
                print(f"  📧 邮箱: {user.email}")
                print(f"  👤 角色: {user.role}")
                print(f"  🔓 激活状态: {user.is_active}")
                print(f"  🔑 密码哈希: {user.hashed_password[:60]}...")
                
                # 测试当前密码
                current_verify = verify_password("123456", user.hashed_password)
                print(f"  🔍 当前密码验证: {'✅ 通过' if current_verify else '❌ 失败'}")
                
                if not current_verify:
                    print(f"  🔧 开始修复密码...")
                    # 生成新的密码哈希
                    new_hash = get_password_hash("123456")
                    
                    # 验证新哈希
                    if not verify_password("123456", new_hash):
                        print(f"  ❌ 新哈希验证失败，退出")
                        sys.exit(1)
                    
                    # 更新用户密码和激活状态
                    user.hashed_password = new_hash
                    user.is_active = True
                    db.commit()
                    db.refresh(user)
                    
                    # 再次验证
                    final_verify = verify_password("123456", user.hashed_password)
                    if final_verify:
                        print(f"  ✅ 密码修复成功！")
                        print(f"  🔑 新密码哈希: {user.hashed_password[:60]}...")
                    else:
                        print(f"  ❌ 密码修复后验证失败")
                        sys.exit(1)
                else:
                    print(f"  ✅ 密码已正确，无需修复")
                    # 确保用户已激活
                    if not user.is_active:
                        user.is_active = True
                        db.commit()
                        print(f"  ✅ 已激活用户")
            else:
                print(f"  ❌ 用户不存在，开始创建...")
                # 创建新用户
                new_hash = get_password_hash("123456")
                if not verify_password("123456", new_hash):
                    print(f"  ❌ 新哈希验证失败")
                    sys.exit(1)
                
                user = User(
                    username=username,
                    email=f"{username}@example.com",
                    hashed_password=new_hash,
                    full_name=full_name,
                    role=role,
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                if verify_password("123456", user.hashed_password):
                    print(f"  ✅ 用户创建成功 (ID: {user.id})")
                else:
                    print(f"  ❌ 用户创建后验证失败")
                    sys.exit(1)
        
        print("\n" + "=" * 60)
        print("✅ 所有用户修复完成！")
        print("=" * 60)
        
        # 最终验证
        print("\n最终验证:")
        for username, _, _ in users_to_fix:
            user = db.query(User).filter(User.username == username).first()
            if user:
                result = verify_password("123456", user.hashed_password)
                status = "✅" if result else "❌"
                active = "已激活" if user.is_active else "未激活"
                print(f"  {status} {username}: 密码验证{'通过' if result else '失败'}, {active}")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()

