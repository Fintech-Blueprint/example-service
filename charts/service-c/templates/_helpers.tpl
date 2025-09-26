{{/* Generate chart name */}}
{{- define "service-c.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "service-c.fullname" -}}
{{- printf "%s-%s" (include "service-c.name" .) .Release.Name -}}
{{- end -}}
