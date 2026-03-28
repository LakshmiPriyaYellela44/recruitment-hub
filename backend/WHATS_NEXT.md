# 🚀 WHAT'S NEXT - DEPLOYMENT & MAINTENANCE GUIDE

## Immediate Next Steps (This Week)

### 1. Local Testing (30 minutes)
```bash
# Terminal 1: Backend
cd d:\recruitment\backend
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
cd d:\recruitment\frontend
npm run dev

# Manual testing in browser: http://localhost:5173
# Follow "Quick Start: 5-Minute Verification" in VERIFICATION_GUIDE.md
```

### 2. Deploy to Staging (1 hour)
```bash
# Commit all changes
git add .
git commit -m "feat: add resume deletion cascade and viewing functionality

- Add resume_id FK and is_derived_from_resume to candidate_skills, experiences, educations
- Implement atomic cascade delete for orphaned records
- Add GET /resumes/{resume_id}/view endpoint for inline display
- Update frontend to view resumes in new browser tab
- Add audit logging for resume operations
- Includes 8 indexes for performance optimization"

# Tag version
git tag v1.0.0-resume-management
git push origin v1.0.0-resume-management

# Deploy to staging
# (Your deployment process here)
```

### 3. Run Integration Tests (30 minutes)
```bash
pytest tests/test_cascade_deletion.py -v --tb=short
pytest tests/test_resume_view.py -v --tb=short

# Check test results
# Expected: All tests passing
```

### 4. Staging Verification (1 hour)
- Upload 2 resumes
- Verify profile shows combined skills
- View resume in new tab
- Delete first resume
- Verify only second resume's data remains
- Check audit logs

---

## Production Deployment (Next Week)

### Pre-Deployment Checklist
```bash
# 1. Backup production database
pg_dump -h prod-db.example.com -U admin recruitment_db > \
  backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Verify migration
python scripts/verify_migration.py --environment production

# 3. Check data consistency
python scripts/check_orphaned_records.py --environment production
# Expected: 0 orphaned records

# 4. Review audit logs
python scripts/export_audit_logs.py --environment production --days 7
# Ensure all operations logged properly
```

### Deployment Steps
```bash
# 1. Deploy code
# Your deployment automation here (Docker, Kubernetes, etc.)

# 2. Run database migration
python manage.py migrate --environment production --single-transaction

# 3. Verify migration success
python scripts/verify_migration.py --environment production

# 4. Restart backend services
kubectl rollout restart deployment/recruitment-backend

# 5. Monitor
kubectl logs -f deployment/recruitment-backend --tail=100

# 6. Smoke test
curl -X GET https://api.example.com/api/candidates/me \
  -H "Authorization: Bearer $(get_test_token)"
```

### Post-Deployment Monitoring (First Week)
```bash
# Monitor key metrics
watch -n 5 "curl -s https://api.example.com/api/health | jq ."

# Check logs for errors
tail -f /var/log/recruitment/backend.log | grep ERROR

# Monitor database performance
psql -h prod-db.example.com -U admin recruitment_db <<EOF
SELECT 
  action,
  COUNT(*) as count,
  MIN(created_at) as first,
  MAX(created_at) as last
FROM audit_logs
WHERE created_at > now() - interval '24 hours'
GROUP BY action
ORDER BY count DESC;
EOF

# Alert thresholds
# - Error rate > 1%
# - Response time > 500ms
# - Database query time > 1s
```

---

## Future Enhancements

### Phase 2: Resume Analytics (2-3 weeks)
```python
# New features:
# 1. Resume parsing statistics
#    - Skills distribution across all users
#    - Common job titles extracted
#    - Years of experience breakdown

# 2. Resume comparison
#    - Side-by-side view of multiple resumes
#    - Highlight differences in skills/experience

# 3. Resume templates
#    - Export profile as PDF from parsed data
#    - Different formatting options

# Implementation plan:
# - Add reporting tables: parsed_skills_stats, job_titles_frequency
# - Add comparison endpoint: GET /resumes/compare?ids=id1,id2
# - Add export endpoint: POST /candidates/me/export-as-pdf
```

### Phase 3: AI-Powered Features (4-6 weeks)
```python
# New features:
# 1. Resume scoring
#    - Match against job description
#    - Skill gap analysis

# 2. Automated recommendations
#    - Suggest missing skills for role
#    - Recommend experience to highlight

# 3. Automated skill extraction improvements
#    - Use NLP for better entity recognition
#    - Categorize skills (technical vs soft skills)

# Implementation plan:
# - Integrate with NLP service (spaCy, transformers)
# - Add endpoint: POST /candidates/me/score-against-job
# - Add endpoint: GET /candidates/me/skill-recommendations
```

### Phase 4: Resume Sharing (2-3 weeks)
```python
# New features:
# 1. Shareable resume links
#    - Generate unique short links
#    - Track who viewed

# 2. Resume versions
#    - Multiple resume versions per candidate
#    - Compare across versions

# 3. Permission-based sharing
#    - Share with recruiters
#    - Grant view/download permissions

# Implementation plan:
# - Add table: resume_shares (link_token, expiration, permissions)
# - Add table: share_views (timestamp, viewer_ip)
# - Add endpoints: POST /resumes/{id}/share, GET /shared/{token}
```

---

## Maintenance Tasks

### Weekly
```bash
# Monitor database
- Check index fragmentation
- Verify backup completion
- Review error logs

# Commands:
pg_stat_user_indexes query -h prod-db.example.com

# Check disk space
df -h /data/postgres

# Review recent errors
tail -n 1000 /var/log/recruitment/backend.log | grep -i error
```

### Monthly
```bash
# Performance review
- Query performance
- Database size growth
- API response times

# SQL:
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname='public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

### Quarterly
```bash
# Index optimization
VACUUM ANALYZE;
REINDEX INDEX CONCURRENTLY idx_candidate_skills_resume_id;
REINDEX INDEX CONCURRENTLY idx_candidate_skills_is_derived;

# Archive old audit logs (keep 1 year)
DELETE FROM audit_logs 
WHERE created_at < now() - interval '1 year';

# Update statistics
ANALYZE;
```

---

## Known Limitations & Future Considerations

### Current Limitations

1. **Single Resume at a Time**
   - Can only upload 1 resume per candidate
   - Future: Support multiple concurrent resumes with versioning

2. **Manual Skill Addition Not Tracked**
   - Manual skills have `is_derived_from_resume=false`
   - Not deletable with resume delete
   - This is intentional - preserve manual data

3. **PDF Viewing Browser Support**
   - Relies on browser's native PDF viewer
   - Some browsers may not support DOCX inline
   - Fallback: Download instead

4. **File Size Limits**
   - Currently limited by S3 upload size
   - Resume files typically < 5MB

### Future Considerations

```python
# 1. Resume Versioning
#    - Support multiple versions
#    - Compare versions
#    - Revert to previous version

# 2. Resume Storage
#    - Archive old resumes
#    - Compress before storage
#    - Encrypt sensitive data

# 3. Resume Processing
#    - Support more file formats (DOC, RTF, HTML)
#    - Better parsing accuracy
#    - Language support (multilingual)

# 4. Resume Sharing
#    - Share directly from platform
#    - Track sharing metrics
#    - Expiring share links

# 5. Integrations
#    - Export to LinkedIn
#    - Import from LinkedIn
#    - Calendar integration (upload dates)
```

---

## Troubleshooting Guide

### Issue: Orphaned Skills After Resume Delete

**Symptom:** After deleting resume, skills still appear in profile

**Diagnosis:**
```sql
SELECT * FROM candidate_skills 
WHERE resume_id IS NOT NULL 
  AND resume_id NOT IN (SELECT id FROM resumes);
```

**If found orphaned records:**
```bash
# Check:
1. Is migration run? 
   SELECT * FROM information_schema.columns 
   WHERE table_name='candidate_skills' AND column_name='resume_id';

2. Was cascade delete executed?
   SELECT * FROM audit_logs 
   WHERE action='RESUME_DELETED_WITH_CASCADE' 
   ORDER BY created_at DESC LIMIT 5;

3. Check error logs during delete
   tail -f /var/log/recruitment/backend.log | grep -A5 "delete_resume"
```

**Fix:**
```sql
-- If critical, manually clean orphaned data:
DELETE FROM candidate_skills 
WHERE resume_id IS NOT NULL 
  AND resume_id NOT IN (SELECT id FROM resumes)
  AND is_derived_from_resume = true;

-- Then investigate what went wrong
```

---

### Issue: Resume View Not Working

**Symptom:** "View" button doesn't open resume

**Diagnosis:**
1. Check browser console for errors
2. Verify endpoint exists: `curl http://localhost:8000/api/resumes/{id}/view`
3. Check authorization headers
4. Verify S3 file exists

**Fix:**
```bash
# 1. Check endpoint
curl -X GET http://localhost:8000/api/health

# 2. Check logs
tail -f /var/log/recruitment/backend.log | grep -i view

# 3. Verify S3 file
aws s3 ls s3://recruitment-bucket/ --recursive | grep {resume_id}

# 4. Test auth
curl -X GET http://localhost:8000/api/resumes/{id}/view \
  -H "Authorization: Bearer {token}" -v
```

---

### Issue: Slow Resume Delete

**Symptom:** Delete takes >5 seconds

**Diagnosis:**
```sql
-- Check index usage
EXPLAIN ANALYZE
DELETE FROM candidate_skills 
WHERE resume_id = 'RESUME_UUID' 
  AND is_derived_from_resume = true;

-- Check data volume
SELECT COUNT(*) FROM candidate_skills 
WHERE is_derived_from_resume = true;
```

**Fix:**
```bash
# Indices might be fragmented
REINDEX INDEX idx_candidate_skills_resume_id;

# Or missing entirely
CREATE INDEX idx_candidate_skills_resume_id ON candidate_skills(resume_id)
WHERE is_derived_from_resume = true;
```

---

## Rollback Procedure

**If critical issue discovered, execute immediately:**

```bash
#!/bin/bash
# ROLLBACK SCRIPT

echo "🚨 INITIATING ROLLBACK..."

# 1. Revert code
git revert -n v1.0.0-resume-management
git commit -m "Revert: resume management features due to critical issue"

# 2. Redeploy previous version
kubectl set image deployment/recruitment-backend \
  recruitment-backend=recruitment-backend:v0.9.9

# 3. Restore database backup (if data corruption)
# pg_restore < backup_YYYYMMDD_HHMMSS.sql

# 4. Verify system
curl -X GET http://localhost:8000/api/health

echo "✅ ROLLBACK COMPLETE"
echo "ℹ️  Investigate cause before redeploying"
```

---

## Support & Documentation

📖 **Documentation Files:**
- `COMPLETE_SOLUTION.md` - Full architecture & design
- `IMPLEMENTATION_GUIDE.md` - Step-by-step code changes
- `RELEASE_NOTES.md` - Deployment guide
- `CHANGES_SUMMARY.md` - Quick reference of all changes
- `VERIFICATION_GUIDE.md` - Test procedures

🐛 **Issues or Questions:**
1. Check documentation first
2. Review audit logs: `SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 50`
3. Check backend logs: `tail -f logs/backend.log`
4. Run diagnostics: `python scripts/diagnose.py`

💾 **Database Info:**
- Host: `{prod-db.example.com}`
- Database: `recruitment_db`
- User: `admin`
- Backup: `s3://backups/recruitment/`

🔗 **Contact:**
- Backend Lead: @backend-team
- DevOps: @devops-team
- Product: @product-team

---

## Success Metrics

**Track these KPIs for 30 days post-deployment:**

```sql
SELECT 
  DATE(created_at) as date,
  COUNT(CASE WHEN action = 'RESUME_UPLOADED' THEN 1 END) as uploads,
  COUNT(CASE WHEN action = 'RESUME_VIEWED' THEN 1 END) as views,
  COUNT(CASE WHEN action = 'RESUME_DELETED_WITH_CASCADE' THEN 1 END) as deletes,
  COUNT(CASE WHEN action LIKE 'ERROR%' THEN 1 END) as errors
FROM audit_logs
WHERE created_at > now() - interval '30 days'
GROUP BY DATE(created_at)
ORDER BY date DESC;
```

**Expected Results:**
- ✅ No orphaned data (0 errors in cascade delete)
- ✅ View functionality used (views > 0)
- ✅ Data consistency maintained (no audit errors)
- ✅ Performance acceptable (no timeout errors)
- ✅ Audit trail complete (all operations logged)

---

## Release Notes

**Version 1.0.0 - Resume Management**

**New Features:**
- Resume viewing in browser tab (GET /resumes/{id}/view)
- Atomic cascade delete for orphaned data
- Resume traceability with resume_id foreign keys

**Improvements:**
- 8 database indexes for query optimization
- Comprehensive audit logging
- Authorization checks on all endpoints

**Fixes:**
- ✅ Orphaned skills/experiences after resume delete
- ✅ No ability to view uploaded resumes
- ✅ Data consistency on cascade operations

**Migration:**
- 18 SQL statements
- 6 new database columns
- 8 new indexes
- Backward compatible

**Deployment:**
- No downtime required
- Safe rollback available
- Estimated time: 15 minutes

**Breaking Changes:**
- None - fully backward compatible

---

## Final Checklist

Before marking as complete:

- [ ] Code reviewed by team
- [ ] All tests passing
- [ ] Staging deployment successful
- [ ] Documentation reviewed
- [ ] Backup verified
- [ ] Rollback procedure documented
- [ ] Team trained on new features
- [ ] Production deployment scheduled
- [ ] Monitoring alerts configured
- [ ] Support team notified

✅ Ready for production!
