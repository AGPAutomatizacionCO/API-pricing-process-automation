# ADR-001 (ACTIVADO por TI): despliegue automático a producción para cambios de personas autorizadas

**Estado:** ACTIVADO por decisión de TI (bmartin, 2026-10-05) para este desarrollo, con el antecedente de otros desarrollos que ya despliegan con GitHub Actions + OIDC.
**Pendiente:** registrar la aprobación formal de Gobierno, Tech Lead y DevOps Owner (ADR-04 del Plan maestro) y cerrar ADR-01; el Plan maestro advierte que esos despliegues existentes demuestran capacidad técnica, no conformidad con la norma para producción.
**Solicitado y autorizado por:** TI (bmartin). **Fecha:** 2026-10-05.

## Contexto
La norma vigente (`agp-ai-governance-kit/harness-policy.md`) dice: *"La IA no puede aprobar producción"* y *"El pipeline debe exigir aprobación manual de IT
antes de desplegar a producción"*. El Plan maestro bloquea la promoción automática a producción hasta cerrar ADR-01 (ejecutor autorizado) y ADR-04
(separación de deberes). Se solicita que los cambios hechos por TI o por la desarrolladora funcional (mgalindo) no necesiten un segundo clic de aprobación.

## Propuesta
Un cambio se despliega a producción sin aprobación manual de entorno **solo si se cumplen todas**:
1. Llegó a `main` por PR con CI en verde (ruleset de `main`: PR obligatorio, checks `test` y `docker-build`).
2. Quien lo integra (`github.actor`) está en la variable `AUTO_DEPLOY_USERS` (propuesta inicial: `BradlyAlejandroAGP` — TI, `Maria-GalindoC` — área funcional).
3. **El cambio no fue asistido por IA** (ningún commit con `Co-Authored-By: Claude/Anthropic` ni "Generated with Claude"): la IA no aprueba producción ni su propio trabajo.
4. Es un `push` a `main`. Los rollbacks y redespliegues manuales (`workflow_dispatch`) siguen exigiendo aprobación.

En cualquier otro caso, el despliegue usa el entorno `prod` con revisor humano obligatorio (comportamiento actual).

## Implementación (en `cd.yml`, ACTIVA)
Job `policy`: elige `prod` o `prod-auto` y deja el motivo en el resumen del run. Está activa con `AUTO_DEPLOY_ENABLED=true` y `AUTO_DEPLOY_USERS` = `BradlyAlejandroAGP`, `Maria-GalindoC`.
Además de las reglas 1 a 4, verifica que el commit pertenezca a un PR (un push directo con permiso de administrador va a aprobación).
Los datos no confiables (autor, mensaje del commit) se pasan por variables de entorno, nunca interpolados en el script.

## Estado de la configuración
1. Entorno GitHub `prod-auto` creado (sin revisores; **solo rama `main`**). HECHO 2026-10-05.
2. Variables `AUTO_DEPLOY_USERS` y `AUTO_DEPLOY_ENABLED=true`. HECHO 2026-10-05.
3. Credencial federada `…:environment:prod-auto`: la crea `infra/setup-oidc.*` junto con las demás. PENDIENTE (script humano).
4. Para desactivar la excepción: `gh variable set AUTO_DEPLOY_ENABLED --body false` (vuelve a aprobación manual en `prod`).
5. Registrar en `deployment-notes.md` quién aprueba producción, la excepción y su vigencia.

## Riesgos y mitigaciones
- Una cuenta autorizada comprometida despliega sin segundo control: exigir 2FA/SSO, PR con CI obligatorio, revisar el resumen de cada run y revisar `AUTO_DEPLOY_USERS` periódicamente.
- El filtro de "asistido por IA" se basa en los trailers del commit: no detecta código de IA copiado sin trailer. Se complementa con la revisión del PR.
- Las credenciales de GitHub de una persona usadas por una herramienta de IA aparecen como esa persona: por eso la regla 3 mira el contenido del commit y no solo el autor.
- ADR-01 sigue abierto: el kit reserva producción a Azure DevOps; esta excepción no sustituye esa decisión.

## Alternativas
A. Mantener aprobación manual siempre (norma actual). B. Aprobar con ventana horaria. C. Auto-despliegue solo a `dev`/`qa` y manual a `prod`.
