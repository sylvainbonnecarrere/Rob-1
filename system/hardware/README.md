# Profils Système

Ce dossier contient les profils matériels générés automatiquement par l'application.

## Fichiers

- `profile_template.json` : Modèle de structure pour les profils
- `*_profile_*.json` : Profils générés automatiquement (ignorés par git)

## Confidentialité

Les profils générés contiennent des informations système sensibles et sont 
automatiquement exclus du contrôle de version via .gitignore.

## Structure du profil

```json
{
  "generated_at": "timestamp",
  "os_info": { "name", "version", "architecture" },
  "python_info": { "version", "executable" },
  "hardware_info": { "cpu_cores", "total_memory_gb", "disk_free_gb" },
  "app_info": { "directory", "script_path", "key_files" }
}
```
