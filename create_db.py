from sqlalchemy import create_engine, ForeignKey, Column, String, Integer, CHAR
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, declarative_base

Base = declarative_base()

class LicensePlates(Base): 
    __tablename__ = "license_plates"

    plate_id = Column("plate_id", Integer, primary_key=True, autoincrement=True)
    plate_text = Column("plate_text", String, nullable=False)

    owner = Column("owner", String, nullable=False)
    car = Column("car", String, nullable=False)
    wanted_license_plates = relationship("WantedLicensePlates", back_populates="license_plate", uselist=False)


class WantedLicensePlates(Base):
    __tablename__ = "wanted_license_plates"

    wanted_id = Column("wanted_id", Integer, primary_key=True, autoincrement=True)
    plate_id = Column(Integer, ForeignKey("license_plates.plate_id"))
    crime_text = Column("crime_text", String)

    license_plate = relationship("LicensePlates", back_populates="wanted_license_plates")

engine = create_engine('sqlite:///car_plates.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)
session = Session()

baleno_mama = LicensePlates(plate_text="JK01AJ0559", owner="Tehmina Yousuf", car="SUZUKI BALENO")
aura_sis = LicensePlates(plate_text="JK01AR3883", owner="UROOJ NISSAR", car="HYUNDAI AURA")

session.add(baleno_mama)
session.add(aura_sis)
session.commit()

wanted_baleno = WantedLicensePlates( plate_id=baleno_mama.plate_id, crime_text="Speeding")

session.add(wanted_baleno)
session.commit()