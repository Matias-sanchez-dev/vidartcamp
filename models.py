from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Date, Time, DateTime, Text
from sqlalchemy.orm import relationship
from database import Base

class Usuario(Base):
    """Usuarios del sistema (administradores y encargados)"""
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String, nullable=False)
    es_admin = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime)


class Torneo(Base):
    """Torneos/Campeonatos"""
    __tablename__ = "torneos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(Text)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date, nullable=True)
    activo = Column(Boolean, default=True)  # Solo un torneo activo a la vez
    mostrar_publico = Column(Boolean, default=True)  # Mostrar en vista pública
    
    # Relationships
    equipos = relationship("Equipo", back_populates="torneo")
    partidos = relationship("Partido", back_populates="torneo")


class Equipo(Base):
    __tablename__ = "equipos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    activo = Column(Boolean, default=True)
    
    # Relación con torneo (nullable para equipos externos)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=True)
    
    # Estadísticas del torneo
    partidos_jugados = Column(Integer, default=0)
    partidos_ganados = Column(Integer, default=0)
    partidos_empatados = Column(Integer, default=0)
    partidos_perdidos = Column(Integer, default=0)
    goles_favor = Column(Integer, default=0)
    goles_contra = Column(Integer, default=0)
    puntos = Column(Integer, default=0)
    
    # Relationships
    torneo = relationship("Torneo", back_populates="equipos")
    jugadores = relationship("Jugador", back_populates="equipo")
    partidos_local = relationship("Partido", foreign_keys="Partido.equipo_local_id", back_populates="equipo_local")
    partidos_visitante = relationship("Partido", foreign_keys="Partido.equipo_visitante_id", back_populates="equipo_visitante")
    
    @property
    def diferencia_goles(self):
        return self.goles_favor - self.goles_contra


class Jugador(Base):
    __tablename__ = "jugadores"
    
    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String, unique=True, index=True, nullable=False)
    nombre_completo = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    equipo_id = Column(Integer, ForeignKey("equipos.id"))
    telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    activo = Column(Boolean, default=True)
    ya_ingreso = Column(Boolean, default=False)  # Previene doble acceso
    
    # Relationships
    equipo = relationship("Equipo", back_populates="jugadores")
    sesiones_qr = relationship("SesionQR", back_populates="jugador")


class Partido(Base):
    __tablename__ = "partidos"
    
    id = Column(Integer, primary_key=True, index=True)
    torneo_id = Column(Integer, ForeignKey("torneos.id"), nullable=True)
    equipo_local_id = Column(Integer, ForeignKey("equipos.id"))
    equipo_visitante_id = Column(Integer, ForeignKey("equipos.id"))
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    
    # Resultados (nullable hasta que se juegue)
    goles_local = Column(Integer, nullable=True)
    goles_visitante = Column(Integer, nullable=True)
    finalizado = Column(Boolean, default=False)
    
    # Información adicional
    cancha = Column(String, nullable=True)
    jornada = Column(Integer, nullable=True)  # Número de fecha/jornada
    notas = Column(Text, nullable=True)
    
    # Relationships
    torneo = relationship("Torneo", back_populates="partidos")
    equipo_local = relationship("Equipo", foreign_keys=[equipo_local_id], back_populates="partidos_local")
    equipo_visitante = relationship("Equipo", foreign_keys=[equipo_visitante_id], back_populates="partidos_visitante")
    goles = relationship("Gol", back_populates="partido", cascade="all, delete-orphan")


class Gol(Base):
    """Goles por jugador en cada partido (para tabla de goleadores)"""
    __tablename__ = "goles"

    id = Column(Integer, primary_key=True, index=True)
    partido_id = Column(Integer, ForeignKey("partidos.id"), index=True, nullable=False)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"), index=True, nullable=False)
    equipo_id = Column(Integer, ForeignKey("equipos.id"), nullable=False)
    cantidad = Column(Integer, default=1, nullable=False)

    # Relationships
    partido = relationship("Partido", back_populates="goles")
    jugador = relationship("Jugador")


class SesionQR(Base):
    __tablename__ = "sesiones_qr"
    
    token = Column(String, primary_key=True, index=True)
    jugador_id = Column(Integer, ForeignKey("jugadores.id"))
    fecha_expiracion = Column(DateTime, nullable=False)
    usado = Column(Boolean, default=False)
    fecha_uso = Column(DateTime, nullable=True)
    
    # Relationships
    jugador = relationship("Jugador", back_populates="sesiones_qr")
