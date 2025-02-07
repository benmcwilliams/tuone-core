```dataview
table location, company, tech, component, status, phase, capacity, investment_value, dt_announce
from "src/phases"
where reject-phase = false and (company = "InnoEnergy-Skills-Institute" or company = "InnoEnergy Skills Institute")
sort location, dt_announce desc
```
