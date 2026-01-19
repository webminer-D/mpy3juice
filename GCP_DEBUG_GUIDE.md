# GCP Debugging Guide for Audio Trimming Issue

## Issue Description
Getting "FFmpeg audio trimming failed: pipe:0: Invalid argument" error on GCP deployment.

## Enhanced Logging Added

### 1. FFmpeg Wrapper Enhancements
- **Detailed command logging**: Full FFmpeg command logged before execution
- **Environment debugging**: PATH, working directory, FFmpeg availability checks
- **Input data validation**: File size, format, and header hex dump
- **Fallback logic**: Automatic fallback from codec copy to re-encoding
- **Enhanced error messages**: More detailed error context and troubleshooting info

### 2. Router Enhancements  
- **Request parameter logging**: All input parameters logged with validation
- **File upload debugging**: Content-type, size, and header information
- **Step-by-step operation tracking**: Each stage of the process logged
- **Error context**: Full request context included in error messages

### 3. Application Logging
- **Startup diagnostics**: Python version, working directory, PATH environment
- **File and console logging**: Logs written to both console and `backend.log` file
- **Debug level logging**: Detailed debug information for audio_tools modules

## Debugging Steps

### Step 1: Check Server Logs
After deploying the enhanced version, check the logs for:

```bash
# Look for startup information
grep "Audio Toolkit API Starting Up" backend.log

# Check FFmpeg availability
grep "FFmpeg found at" backend.log

# Look for environment issues
grep "Environment PATH" backend.log
```

### Step 2: Test with Debug Script
Use the provided debug script to test the endpoint:

```bash
# Test your GCP deployment
python debug_trim_issue.py https://your-gcp-url.com

# Test with specific audio file
python debug_trim_issue.py https://your-gcp-url.com your_audio.mp3
```

### Step 3: Analyze Trim Request Logs
Look for detailed trim request logs:

```bash
# Find trim requests
grep "Trim request:" backend.log

# Check FFmpeg command execution
grep "FFmpeg command:" backend.log

# Look for fallback attempts
grep "Falling back to re-encoding" backend.log
```

## Common Issues and Solutions

### Issue 1: FFmpeg Not Found
**Symptoms**: "FFmpeg not found at: ffmpeg"
**Solution**: Install FFmpeg on GCP instance or update PATH

### Issue 2: Codec Copy Issues
**Symptoms**: "pipe:0: Invalid argument" with codec copy
**Solution**: Enhanced version automatically falls back to re-encoding

### Issue 3: Input Format Issues
**Symptoms**: Format detection or validation errors
**Solution**: Check file header hex dump in logs for corruption

### Issue 4: Memory/Resource Issues
**Symptoms**: Timeout or resource exhaustion
**Solution**: Check file sizes and server resources

## Log Analysis Examples

### Successful Request Log Pattern:
```
INFO - Trim request: audio.mp3 from 0.5s to 1.5s
INFO - Detected input format: mp3
INFO - File data read successfully: 16526 bytes
DEBUG - File header (hex): 494433030000000...
INFO - Starting FFmpeg trimming operation...
INFO - FFmpeg command: ffmpeg -i pipe:0 -ss 0.5 -t 1.0 -c copy -f mp3 pipe:1
INFO - FFmpeg audio trimming (codec copy) completed successfully
```

### Failed Request with Fallback Log Pattern:
```
INFO - Trim request: audio.mp3 from 0.5s to 1.5s
WARNING - Codec copy failed: FFmpeg audio trimming failed: pipe:0: Invalid argument
INFO - Falling back to re-encoding for trimming
INFO - FFmpeg command: ffmpeg -i pipe:0 -ss 0.5 -t 1.0 -codec:a libmp3lame -b:a 192k -f mp3 pipe:1
INFO - FFmpeg audio trimming (re-encode) completed successfully
```

## Next Steps

1. **Deploy enhanced version** with comprehensive logging
2. **Run debug script** against GCP deployment
3. **Analyze logs** using patterns above
4. **Check specific error messages** for root cause
5. **Apply targeted fixes** based on log analysis

The enhanced logging will provide much more detailed information about what's happening during the FFmpeg execution, making it easier to identify and fix the root cause of the "pipe:0: Invalid argument" error.