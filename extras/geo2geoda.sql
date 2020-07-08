-- Este script migra los datos de la antigua aplicación de GEO a la nueva.

SET FOREIGN_KEY_CHECKS=0;
TRUNCATE geoda2.profesor_curso;
TRUNCATE geoda2.curso;
TRUNCATE geoda2.forano;
DELETE FROM geoda2.social_auth_usersocialauth WHERE user_id > 1;
DELETE FROM geoda2.accounts_customuser_groups WHERE customuser_id > 1;
DELETE FROM geoda2.django_admin_log WHERE user_id > 1;
DELETE FROM geoda2.accounts_customuser WHERE id > 1;
-- TRUNCATE geoda2.asignatura;
TRUNCATE geoda2.categoria;
-- TRUNCATE geoda2.pod;
SET FOREIGN_KEY_CHECKS=1;

/* -- Esta tabla es actualizada por una pasarela ETL (Pentaho Spoon)
INSERT INTO geoda2.pod (plan_id_nk, centro_id, asignatura_id, cod_grupo_asignatura, anyo_academico, nip, apellido1, apellido2, nombre, tipo_docencia)
SELECT DISTINCT codigo_plan,cod_centro, codigo_asignatura, cod_grupo_asignatura, ano_academico, nip, primer_apellido, segundo_apellido, nombre, tipo_docencia
FROM add_geodb.Pod;
*/

SET FOREIGN_KEY_CHECKS=0;
INSERT INTO geoda2.categoria(id, plataforma_id, id_nk, nombre, centro_id, plan_id_nk, anyo_academico, supercategoria_id)
SELECT id,plataformaId,idExterno,nombre,codigoCentro,codigoPlan,anoAcademico,categoriaPadreId
FROM add_geodb.Categoria;
SET FOREIGN_KEY_CHECKS=1;

/* -- Esta tabla es actualizada por una pasarela ETL (Pentaho Spoon)
INSERT INTO geoda2.asignatura(id, plan_id_nk, nombre_estudio, centro_id, nombre_centro, tipo_estudio_id, nombre_tipo_estudio, asignatura_id, nombre_asignatura, prela_cu, tipo_periodo, valor_periodo, cod_grupo_asignatura, turno, tipo_docencia, anyo_academico, edicion)
SELECT id, codigo_plan, descripcion, cod_centro, nombreCentro, tipo_estudio, nombreTipoEstudio, codigo_asignatura, nombreAsignatura, prela_cu, tipo_periodo, valor_periodo, cod_grupo_asignatura, turno, tipo_docencia, ano_academico, edicion
FROM add_geodb.CursoSigma;
*/

UPDATE add_geodb.User SET lastvisit_at=NULL WHERE lastvisit_at='0000-00-00 00:00:00';

-- No se han recogido los roles (admin, gestor, profesor, forano)
INSERT INTO geoda2.accounts_customuser (id,username,password,email,date_joined,last_login,is_superuser,is_active,first_name,last_name,is_staff)
SELECT id,username,password,email,create_at,lastvisit_at,superuser,status,firstname,lastname,0
FROM add_geodb.User
JOIN add_geodb.Profile ON User.id=Profile.user_id
WHERE id>1;

-- SELECT DISTINCT username FROM accounts_customuser WHERE username RLIKE '^[0-9]*$';
INSERT INTO geoda2.social_auth_usersocialauth (provider,uid,extra_data,user_id)
SELECT 'saml', CONCAT('lord:', username), '{}', id
FROM geoda2.accounts_customuser
WHERE username RLIKE '^[0-9]*$';


SET FOREIGN_KEY_CHECKS=0;

INSERT INTO geoda2.curso (id,nombre,fecha_solicitud,fecha_autorizacion,plataforma_id,id_nk,fecha_creacion,url,anyo_academico,motivo_solicitud,comentarios,asignatura_id,autorizador_id,categoria_id,estado)
SELECT id,nombre,fechaSolicitud,fechaAutorizacion,plataformaId,codigoEnPlataforma,fechaCreacion,url,anoAcademico,motivoSolicitud,motivoDenegacion,cursoSigmaId,autorizadorId,categoriaId,estado
FROM add_geodb.Curso;

UPDATE add_geodb.ProfesorCurso SET fechaBaja=NULL WHERE fechaBaja='';
INSERT INTO geoda2.profesor_curso(id, fecha_alta, fecha_baja, curso_id, profesor_id)
SELECT id, fechaAlta, STR_TO_DATE(fechaBaja, '%e/%c/%Y %H:%i:%s'), cursoId, userId
FROM add_geodb.ProfesorCurso;

SET FOREIGN_KEY_CHECKS=1;
