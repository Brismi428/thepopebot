# NCA Toolkit Transcription Report

## Job Details
- **Date**: February 13, 2026
- **Task**: Transcribe YouTube video using NCA Toolkit
- **Video URL**: https://www.youtube.com/watch?v=zeJ4whgLELE
- **Service**: https://media.wat-factory.cloud

## Executive Summary

**Status**: ❌ FAILED - Service Configuration Issue

The NCA Toolkit API is operational but experiencing S3 authorization errors that prevent all media processing operations from completing. The service successfully accepts requests and begins processing but fails when attempting to upload results to S3 storage.

## Investigation Steps

### 1. Service Discovery
- Located NCA Toolkit documentation in `/job/config/mcp_registry.md`
- Confirmed API base URL: `https://media.wat-factory.cloud`
- Confirmed authentication method: `x-api-key` header with `NCA_API_KEY`

### 2. API Endpoint Testing

#### Test /v1/media/transcribe (Direct URL)
**Request**:
```json
POST /v1/media/transcribe
{
  "media_url": "https://www.youtube.com/watch?v=zeJ4whgLELE"
}
```

**Response**: HTTP 500
```json
{
  "code": 500,
  "job_id": "91adae03-7146-4fee-b4db-b2a64b27918a",
  "message": "Failed to load audio: ... Error opening input file ... .html. Error opening input files: Invalid data found when processing input"
}
```

**Analysis**: The service attempted to download the YouTube URL but received HTML instead of media content. This indicates the YouTube URL handler is not working correctly - likely needs yt-dlp integration.

#### Test /v1/BETA/media/download
**Request**:
```json
POST /v1/BETA/media/download
{
  "media_url": "https://www.youtube.com/watch?v=zeJ4whgLELE"
}
```

**Response**: HTTP 500
```json
{
  "code": 500,
  "job_id": "da7ba9e2-1fe0-4943-b198-c7a57f215481",
  "message": "An error occurred (Unauthorized) when calling the CreateMultipartUpload operation: Unauthorized"
}
```

**Analysis**: The service successfully initiated the download process but failed when trying to upload the result to S3. This is an S3 credentials/permissions issue.

#### Test /v1/toolkit/test
**Response**: HTTP 500 - Same S3 Unauthorized error

### 3. Root Cause Analysis

The NCA Toolkit service has **misconfigured or missing S3 credentials**:

1. All endpoints that attempt to write to S3 fail with "Unauthorized" errors
2. The service can receive requests and begin processing
3. Processing fails at the storage/upload stage
4. This affects:
   - Media downloads
   - Transcription results
   - Test endpoint validation

### 4. Service Configuration Details

**Build Number**: 219  
**API Endpoints Tested**:
- ✅ Service is reachable
- ✅ API key authentication works
- ✅ Job queueing works
- ❌ S3 upload fails (missing/invalid AWS credentials)

## Impact

- **Transcription**: Cannot complete (result storage fails)
- **Media Download**: Cannot complete (download storage fails)
- **All Media Processing**: Blocked by S3 issue

## Required Actions

### Immediate (Service Owner)
1. Configure valid AWS S3 credentials on the NCA Toolkit server
2. Verify S3 bucket permissions for:
   - CreateMultipartUpload
   - PutObject
   - GetObject operations
3. Test endpoints after credential configuration

### Alternative Approaches (User)

Since the NCA Toolkit is currently unavailable, here are alternatives for transcribing the YouTube video:

1. **OpenAI Whisper API**
   - Download video with yt-dlp
   - Extract audio
   - Use OpenAI Whisper API directly

2. **AssemblyAI**
   - Supports direct YouTube URLs
   - Handles download internally

3. **Local Whisper**
   - Install whisper locally
   - Process audio file directly

4. **Google Cloud Speech-to-Text**
   - Upload audio to GCS
   - Use Speech-to-Text API

## Technical Details

### API Schema (from mcp_registry.md)

**Transcribe Endpoint**:
```
POST /v1/media/transcribe
Headers: x-api-key: <NCA_API_KEY>
Body: {
  "media_url": "<URL to audio/video>",
  "output": "text" | "srt" | "vtt"  # Optional, defaults to text
}
```

**Download Endpoint**:
```
POST /v1/BETA/media/download
Headers: x-api-key: <NCA_API_KEY>
Body: {
  "media_url": "<YouTube or other URL>",
  "quality": "best" | "worst" | specific format
}
```

### Error Patterns

All failed requests show:
- `queue_time`: 0 (requests processed immediately)
- `run_time`: 0.5 - 7 seconds (processing started)
- `code`: 500 (internal server error)
- `message`: S3 "Unauthorized" or FFmpeg input errors

## Video Information

**YouTube Video**: https://www.youtube.com/watch?v=zeJ4whgLELE

To transcribe this video once the NCA Toolkit is fixed, use:
```bash
curl -X POST https://media.wat-factory.cloud/v1/media/transcribe \
  -H "x-api-key: $NCA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"media_url":"https://www.youtube.com/watch?v=zeJ4whgLELE"}'
```

## Recommendations

1. **For Service Owner**: Priority fix - configure S3 credentials
2. **For Users**: Use alternative transcription services until fixed
3. **For Future**: Add health check endpoint that validates S3 connectivity
4. **For Monitoring**: Implement alerts for S3 authorization failures

## Files Generated

- `/job/tmp/transcribe_response.json` - Last API response (500 error)
- `/job/tmp/NCA_TOOLKIT_TRANSCRIPTION_REPORT.md` - This report

## Contact

If you maintain the NCA Toolkit service, the S3 configuration issue needs to be addressed before the service can process any media files.

---
*Report generated by WAT Factory Bot*  
*Job ID: [Current Job]*  
*Date: February 13, 2026 13:14 UTC*
