from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from geo.models import Curso, RightsSupport, Asignatura, Categoria, ProfesorCurso

User = get_user_model()


class MassTeacherEnrollmentTest(TestCase):
    def setUp(self):
        # Create users
        self.admin = User.objects.create_superuser(username="admin", password="password")
        self.staff_user = User.objects.create_user(
            username="staff", password="password", is_staff=True
        )
        self.normal_user = User.objects.create_user(username="user", password="password")

        # Create a Categoria
        self.categoria = Categoria.objects.create(
            id=1,
            plataforma_id=1,
            id_nk="1",
            nombre="Categoria de Prueba",
            anyo_academico=2026,
        )

        # Create an Asignatura
        self.asignatura = Asignatura.objects.create(
            id=123,
            plan_id_nk=555,
            nombre_estudio="Estudio de Prueba",
            centro_id=1,
            nombre_centro="Centro de Prueba",
            asignatura_id=12345,
            nombre_asignatura="Asignatura de Prueba",
            cod_grupo_asignatura=1,
            anyo_academico=2026,
        )

        # Create a course
        self.curso = Curso.objects.create(
            id=12345,
            nombre="Curso de Prueba",
            estado=Curso.Estado.CREADO,
            plataforma_id=1,
            anyo_academico=2026,
            id_nk="999",
            asignatura=self.asignatura,
            categoria=self.categoria,
        )

        # Add the custom permission to staff_user
        content_type = ContentType.objects.get_for_model(RightsSupport)
        self.permission = Permission.objects.get(
            codename="anyadir_profesores_masivo",
            content_type=content_type,
        )
        self.staff_user.user_permissions.add(self.permission)

    def test_permission_required(self):
        # A user without the permission gets a 403 Forbidden
        self.client.login(username="user", password="password")
        url = reverse('curso_matricular_profesores_masivo')
        response = self.client.post(url, {'curso_id': self.curso.id})
        self.assertEqual(response.status_code, 403)

    def test_permission_without_being_teacher(self):
        # A user with the permission but who is NOT a teacher of the course gets a 403 Forbidden
        self.client.login(username="staff", password="password")
        url = reverse('curso_matricular_profesores_masivo')
        response = self.client.post(url, {'curso_id': self.curso.id})
        self.assertEqual(response.status_code, 403)

    @patch('geo.models.WSClient')
    @patch('accounts.models.get_identidad')
    def test_mass_enrollment_success(self, mock_get_identidad, mock_ws_client_class):
        # Mock WSClient instance
        mock_ws_instance = mock_ws_client_class.return_value
        mock_ws_instance.buscar_usuario_nip.return_value = {'id': 111}
        mock_ws_instance.matricular_profesor.return_value = {}

        # Add staff_user as a teacher of the course
        ProfesorCurso.objects.create(
            curso=self.curso, profesor=self.staff_user, fecha_alta=timezone.now()
        )

        # Mock the get_identidad pipeline to just set some user attributes
        def fake_get_identidad(strategy, details, user, *args, **kwargs):
            user.first_name = "Profesor"
            user.last_name = user.username
            user.email = f"{user.username}@example.com"
            user.colectivos = '["PDI"]'
            user.save()
            return {'user': user}

        mock_get_identidad.side_effect = fake_get_identidad

        self.client.login(username="staff", password="password")

        # Create a CSV file content with NIPs
        csv_content = b"900001\n900002\n"
        uploaded_file = SimpleUploadedFile("profesores.csv", csv_content, content_type="text/csv")

        url = reverse('curso_matricular_profesores_masivo')
        response = self.client.post(url, {'curso_id': self.curso.id, 'file': uploaded_file})

        # It should redirect back to course detail
        self.assertRedirects(response, reverse('curso_detail', args=[self.curso.id]))

        # Verify that the two users were created in the database and added as active teachers
        user1 = User.objects.get(username="900001")
        user2 = User.objects.get(username="900002")
        self.assertEqual(user1.email, "900001@example.com")
        self.assertEqual(user2.email, "900002@example.com")

        # Verify they are in the course's active teachers
        self.assertIn(user1, self.curso.profesores_activos)
        self.assertIn(user2, self.curso.profesores_activos)

