```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "Abu-Dhabi-National-Energy-Company,-PJSC-(TAQA)" or company = "Abu Dhabi National Energy Company, PJSC (TAQA)")
sort location, dt_announce desc
```
