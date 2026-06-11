#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""文件浏览器 API：列表、上传、下载、新建、更名、删除"""
import os, shutil
from flask import jsonify, request, send_file

from .utils import resolve_path, safe_path, is_protected, is_external_dir, BASE_DIR


def register(app) -> None:
    @app.route("/api/files")
    def api_files_list():
        path = request.args.get("path", "")
        abs_path, ok = resolve_path(path)
        if not ok:
            return jsonify({"status": "error", "message": "访问被拒绝"}), 403
        if not path:
            try:
                items = []
                for name in sorted(os.listdir(abs_path)):
                    full = os.path.join(abs_path, name)
                    rel = os.path.relpath(full, BASE_DIR)
                    items.append({
                        "name": name, "path": rel.replace("\\", "/"),
                        "dir": os.path.isdir(full),
                        "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                    })
                return jsonify({"status": "ok", "items": items, "cwd": path or "."})
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        if not os.path.exists(abs_path):
            return jsonify({"status": "error", "message": "路径不存在"}), 404
        if not os.path.isdir(abs_path):
            return jsonify({"status": "error", "message": "不是目录"}), 400
        try:
            items = []
            for name in sorted(os.listdir(abs_path)):
                full = os.path.join(abs_path, name)
                items.append({
                    "name": name, "path": path + "/" + name,
                    "dir": os.path.isdir(full),
                    "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                })
            return jsonify({"status": "ok", "items": items, "cwd": path})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/files/download")
    def api_files_download():
        path = request.args.get("path", "")
        abs_path, ok = resolve_path(path)
        if not ok:
            return "", 403
        if not os.path.isfile(abs_path):
            return "", 404
        return send_file(abs_path, as_attachment=True, download_name=os.path.basename(abs_path))

    @app.route("/api/files/upload", methods=["POST"])
    def api_files_upload():
        path = request.args.get("path", ".")
        abs_dir, ok = resolve_path(path)
        if not ok:
            return jsonify({"status": "error", "message": "访问被拒绝"}), 403
        if not os.path.isdir(abs_dir):
            return jsonify({"status": "error", "message": "目录不存在"}), 404
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "未选择文件"}), 400
        f = request.files["file"]
        if f.filename == "":
            return jsonify({"status": "error", "message": "文件名为空"}), 400
        try:
            f.save(os.path.join(abs_dir, f.filename))
            return jsonify({"status": "ok", "message": f"已上传: {f.filename}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/files/mkdir", methods=["POST"])
    def api_files_mkdir():
        data = request.get_json(force=True)
        path = data.get("path", "")
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "文件夹名不能为空"}), 400
        abs_dir = safe_path(path)
        if not abs_dir:
            return jsonify({"status": "error", "message": "访问被拒绝"}), 403
        try:
            os.makedirs(os.path.join(abs_dir, name), exist_ok=True)
            return jsonify({"status": "ok", "message": f"已创建: {name}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/files/rename", methods=["POST"])
    def api_files_rename():
        data = request.get_json(force=True)
        path = data.get("path", "")
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"status": "error", "message": "新名称不能为空"}), 400
        abs_path = safe_path(path)
        if not abs_path:
            return jsonify({"status": "error", "message": "访问被拒绝"}), 403
        if is_external_dir(path):
            return jsonify({"status": "error", "message": "该目录不允许更名"}), 403
        if is_protected(abs_path) and not data.get("force"):
            return jsonify({"status": "error", "message": "该文件受保护，无法更名"}), 403
        try:
            new_path = os.path.join(os.path.dirname(abs_path), name)
            shutil.move(abs_path, new_path)
            return jsonify({"status": "ok", "message": f"已更名: {os.path.basename(abs_path)} → {name}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    @app.route("/api/files/delete", methods=["POST"])
    def api_files_delete():
        data = request.get_json(force=True)
        path = data.get("path", "")
        abs_path = safe_path(path)
        if not abs_path:
            return jsonify({"status": "error", "message": "访问被拒绝"}), 403
        if is_external_dir(path):
            return jsonify({"status": "error", "message": "该目录不允许删除"}), 403
        if is_protected(abs_path) and not data.get("force"):
            return jsonify({"status": "error", "message": "该文件受保护，无法删除"}), 403
        try:
            name = os.path.basename(abs_path)
            if os.path.isdir(abs_path):
                os.rmdir(abs_path)
            else:
                os.remove(abs_path)
            return jsonify({"status": "ok", "message": f"已删除: {name}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
