/* ============================================================
   PULSE STUDIO — Face Sidebar Thumbnails
   Exact 120×80 Miniaturized Vector Representations of Faces
   ============================================================ */

/**
 * Returns an SVG string representing the miniaturized face layout.
 * ViewBox: 0 0 120 80
 */
export function renderThumbnail(faceId, accentColor = '#ffffff') {
  const lineCol = '#262626';
  const dimCol = '#555555';
  const dotOff = '#1c1c1c';

  switch (faceId) {
    case 'dual':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <!-- Top headers -->
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">CPU</text>
          <text x="44" y="14" fill="${dimCol}" font-family="monospace" font-size="5">4.2G</text>
          
          <text x="68" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">GPU</text>
          <text x="100" y="14" fill="${dimCol}" font-family="monospace" font-size="5">185W</text>

          <!-- Middle Divider -->
          <line x1="60" y1="6" x2="60" y2="74" stroke="${lineCol}" stroke-width="1"/>

          <!-- CPU Numerals 28 -->
          <text x="10" y="38" fill="${accentColor}" font-family="monospace" font-size="18" font-weight="900" letter-spacing="-1">28</text>
          <text x="36" y="28" fill="${dimCol}" font-family="monospace" font-size="8">%</text>

          <!-- GPU Numerals 42 -->
          <text x="68" y="38" fill="${accentColor}" font-family="monospace" font-size="18" font-weight="900" letter-spacing="-1">42</text>
          <text x="94" y="28" fill="${dimCol}" font-family="monospace" font-size="8">%</text>

          <!-- Dot bars -->
          <g transform="translate(10, 44)">
            ${Array.from({ length: 12 }, (_, i) => `<circle cx="${i * 3.8 + 1}" cy="2" r="1.2" fill="${i < 4 ? accentColor : dotOff}"/>`).join('')}
          </g>
          <g transform="translate(68, 44)">
            ${Array.from({ length: 12 }, (_, i) => `<circle cx="${i * 3.8 + 1}" cy="2" r="1.2" fill="${i < 6 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <!-- Horizontal rules -->
          <line x1="8" y1="52" x2="52" y2="52" stroke="${lineCol}" stroke-width="1"/>
          <line x1="68" y1="52" x2="112" y2="52" stroke="${lineCol}" stroke-width="1"/>

          <!-- Bottom temps -->
          <text x="10" y="62" fill="${dimCol}" font-family="monospace" font-size="4">TEMP</text>
          <text x="10" y="72" fill="${accentColor}" font-family="monospace" font-size="9" font-weight="bold">54°</text>

          <text x="68" y="62" fill="${dimCol}" font-family="monospace" font-size="4">TEMP</text>
          <text x="68" y="72" fill="${accentColor}" font-family="monospace" font-size="9" font-weight="bold">49°</text>
        </svg>
      `;

    case 'cpu':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">CPU GRID</text>
          <text x="82" y="14" fill="${dimCol}" font-family="monospace" font-size="5">4.2 GHZ</text>
          <line x1="8" y1="18" x2="112" y2="18" stroke="${lineCol}" stroke-width="1"/>

          <text x="10" y="44" fill="${accentColor}" font-family="monospace" font-size="24" font-weight="900" letter-spacing="-1">28</text>
          <text x="46" y="32" fill="${dimCol}" font-family="monospace" font-size="10">%</text>

          <g transform="translate(10, 50)">
            ${Array.from({ length: 22 }, (_, i) => `<circle cx="${i * 4.6 + 1.5}" cy="2" r="1.4" fill="${i < 7 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <line x1="8" y1="58" x2="112" y2="58" stroke="${lineCol}" stroke-width="1"/>
          <text x="10" y="68" fill="${dimCol}" font-family="monospace" font-size="4">TEMP</text>
          <text x="10" y="76" fill="${accentColor}" font-family="monospace" font-size="8" font-weight="bold">54°C</text>

          <text x="80" y="68" fill="${dimCol}" font-family="monospace" font-size="4">STATUS</text>
          <text x="80" y="76" fill="${dimCol}" font-family="monospace" font-size="7" font-weight="bold">NORMAL</text>
        </svg>
      `;

    case 'gpu':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">GPU GRID</text>
          <text x="86" y="14" fill="${dimCol}" font-family="monospace" font-size="5">185 W</text>
          <line x1="8" y1="18" x2="112" y2="18" stroke="${lineCol}" stroke-width="1"/>

          <text x="10" y="44" fill="${accentColor}" font-family="monospace" font-size="24" font-weight="900" letter-spacing="-1">42</text>
          <text x="46" y="32" fill="${dimCol}" font-family="monospace" font-size="10">%</text>

          <g transform="translate(10, 50)">
            ${Array.from({ length: 22 }, (_, i) => `<circle cx="${i * 4.6 + 1.5}" cy="2" r="1.4" fill="${i < 10 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <line x1="8" y1="58" x2="112" y2="58" stroke="${lineCol}" stroke-width="1"/>
          <text x="10" y="68" fill="${dimCol}" font-family="monospace" font-size="4">TEMP</text>
          <text x="10" y="76" fill="${accentColor}" font-family="monospace" font-size="8" font-weight="bold">49°C</text>

          <text x="80" y="68" fill="${dimCol}" font-family="monospace" font-size="4">STATUS</text>
          <text x="80" y="76" fill="${dimCol}" font-family="monospace" font-size="7" font-weight="bold">NORMAL</text>
        </svg>
      `;

    case 'ram':
    case 'memory':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="10" y="13" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">MEMORY</text>
          <text x="80" y="13" fill="${dimCol}" font-family="monospace" font-size="5">32 GB</text>
          <line x1="8" y1="16" x2="112" y2="16" stroke="${lineCol}" stroke-width="1"/>

          <text x="10" y="36" fill="${accentColor}" font-family="monospace" font-size="18" font-weight="900">56</text>
          <text x="36" y="28" fill="${dimCol}" font-family="monospace" font-size="7">%</text>
          <text x="64" y="34" fill="${dimCol}" font-family="monospace" font-size="5">RAM IN USE</text>

          <line x1="8" y1="42" x2="112" y2="42" stroke="${lineCol}" stroke-width="1"/>

          <!-- USED row -->
          <text x="10" y="53" fill="${accentColor}" font-family="monospace" font-size="5" font-weight="bold">USED</text>
          <g transform="translate(28, 50)">
            ${Array.from({ length: 14 }, (_, i) => `<circle cx="${i * 4 + 1}" cy="2" r="1.1" fill="${i < 8 ? accentColor : dotOff}"/>`).join('')}
          </g>
          <text x="90" y="53" fill="${dimCol}" font-family="monospace" font-size="5">17.9G</text>

          <line x1="8" y1="60" x2="112" y2="60" stroke="${lineCol}" stroke-width="1"/>

          <!-- FREE row -->
          <text x="10" y="71" fill="${dimCol}" font-family="monospace" font-size="5">FREE</text>
          <g transform="translate(28, 68)">
            ${Array.from({ length: 14 }, (_, i) => `<circle cx="${i * 4 + 1}" cy="2" r="1.1" fill="${i < 6 ? dimCol : dotOff}"/>`).join('')}
          </g>
          <text x="90" y="71" fill="${dimCol}" font-family="monospace" font-size="5">14.1G</text>
        </svg>
      `;

    case 'thermal':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">CPU</text>
          <text x="44" y="14" fill="${dimCol}" font-family="monospace" font-size="5">TCTL</text>
          
          <text x="68" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">GPU</text>
          <text x="100" y="14" fill="${dimCol}" font-family="monospace" font-size="5">EDGE</text>

          <line x1="60" y1="6" x2="60" y2="74" stroke="${lineCol}" stroke-width="1"/>

          <!-- CPU Temp 54° -->
          <text x="10" y="38" fill="${accentColor}" font-family="monospace" font-size="18" font-weight="900" letter-spacing="-1">54</text>
          <text x="36" y="28" fill="${dimCol}" font-family="monospace" font-size="8">°C</text>

          <!-- GPU Temp 49° -->
          <text x="68" y="38" fill="${accentColor}" font-family="monospace" font-size="18" font-weight="900" letter-spacing="-1">49</text>
          <text x="94" y="28" fill="${dimCol}" font-family="monospace" font-size="8">°C</text>

          <g transform="translate(10, 44)">
            ${Array.from({ length: 12 }, (_, i) => `<circle cx="${i * 3.8 + 1}" cy="2" r="1.2" fill="${i < 6 ? accentColor : dotOff}"/>`).join('')}
          </g>
          <g transform="translate(68, 44)">
            ${Array.from({ length: 12 }, (_, i) => `<circle cx="${i * 3.8 + 1}" cy="2" r="1.2" fill="${i < 5 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <line x1="8" y1="52" x2="52" y2="52" stroke="${lineCol}" stroke-width="1"/>
          <line x1="68" y1="52" x2="112" y2="52" stroke="${lineCol}" stroke-width="1"/>

          <text x="10" y="62" fill="${dimCol}" font-family="monospace" font-size="4">THERMAL</text>
          <text x="10" y="72" fill="${dimCol}" font-family="monospace" font-size="6" font-weight="bold">NORMAL</text>

          <text x="68" y="62" fill="${dimCol}" font-family="monospace" font-size="4">THERMAL</text>
          <text x="68" y="72" fill="${dimCol}" font-family="monospace" font-size="6" font-weight="bold">NORMAL</text>
        </svg>
      `;

    case 'network':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="7" font-weight="bold">NETWORK</text>
          <text x="88" y="14" fill="${dimCol}" font-family="monospace" font-size="5">ETH0</text>
          <line x1="8" y1="18" x2="112" y2="18" stroke="${lineCol}" stroke-width="1"/>

          <!-- Upload col -->
          <text x="10" y="27" fill="${accentColor}" font-family="monospace" font-size="5" font-weight="bold">↑ UP</text>
          <text x="10" y="44" fill="${accentColor}" font-family="monospace" font-size="16" font-weight="900" letter-spacing="-1">12</text>
          <text x="10" y="51" fill="${dimCol}" font-family="monospace" font-size="4">MB/S</text>

          <!-- Download col -->
          <text x="110" y="27" fill="${accentColor}" font-family="monospace" font-size="5" font-weight="bold" text-anchor="end">DOWN ↓</text>
          <text x="110" y="44" fill="${accentColor}" font-family="monospace" font-size="16" font-weight="900" letter-spacing="-1" text-anchor="end">84</text>
          <text x="110" y="51" fill="${dimCol}" font-family="monospace" font-size="4" text-anchor="end">MB/S</text>

          <!-- Shared Throughput Bar -->
          <g transform="translate(10, 56)">
            ${Array.from({ length: 22 }, (_, i) => `<circle cx="${i * 4.6 + 1.5}" cy="2" r="1.3" fill="${i < 9 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <line x1="8" y1="63" x2="112" y2="63" stroke="${lineCol}" stroke-width="1"/>
          <text x="10" y="73" fill="${dimCol}" font-family="monospace" font-size="4.5">PEAK 48 / 212</text>
          <circle cx="86" cy="71.5" r="1.5" fill="${accentColor}"/>
          <text x="91" y="73" fill="${accentColor}" font-family="monospace" font-size="4.5" font-weight="bold">ONLINE</text>
        </svg>
      `;

    case 'clock':
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <!-- Top Header -->
          <text x="10" y="14" fill="${accentColor}" font-family="monospace" font-size="6" font-weight="bold">CLOCK</text>
          <text x="110" y="14" fill="${dimCol}" font-family="monospace" font-size="4" text-anchor="end">LOCAL · UTC+3:30</text>

          <!-- Big Time -->
          <text x="32" y="42" fill="${accentColor}" font-family="monospace" font-size="20" font-weight="900" letter-spacing="-1" text-anchor="middle">10</text>
          <circle cx="48" cy="33" r="1.5" fill="#d71921"/>
          <circle cx="48" cy="39" r="1.5" fill="#d71921"/>
          <text x="64" y="42" fill="${accentColor}" font-family="monospace" font-size="20" font-weight="900" letter-spacing="-1" text-anchor="middle">42</text>
          <text x="80" y="34" fill="${accentColor}" font-family="monospace" font-size="5" font-weight="bold">AM</text>
          <text x="80" y="41" fill="#333333" font-family="monospace" font-size="5" font-weight="bold">PM</text>

          <!-- Seconds dots row -->
          <g transform="translate(10, 48)">
            ${Array.from({ length: 30 }, (_, i) => `<circle cx="${i * 3.4 + 1}" cy="2" r="0.9" fill="${i === 14 ? '#d71921' : i < 14 ? '#3a3a3a' : dotOff}"/>`).join('')}
          </g>

          <!-- Footer -->
          <line x1="8" y1="56" x2="112" y2="56" stroke="${lineCol}" stroke-width="1"/>
          <text x="10" y="65" fill="${accentColor}" font-family="monospace" font-size="5" font-weight="bold">WED</text>
          <text x="24" y="65" fill="${dimCol}" font-family="monospace" font-size="4.5">25 SEP 2026</text>
          <text x="110" y="65" fill="${dimCol}" font-family="monospace" font-size="4.5" text-anchor="end">TIME <tspan fill="${accentColor}" font-weight="bold">42</tspan></text>

          <!-- TE Ruler ticks -->
          <g transform="translate(10, 70)">
            ${Array.from({ length: 24 }, (_, i) => `<rect x="${i * 4.2}" y="${i % 4 === 0 ? 0 : 2}" width="1" height="${i % 4 === 0 ? 5 : 3}" fill="${i % 4 === 0 ? '#333333' : '#1e1e1e'}"/>`).join('')}
          </g>
        </svg>
      `;

    case 'minimal':
    default:
      return `
        <svg viewBox="0 0 120 80" width="100%" height="100%" style="display:block;">
          <text x="60" y="14" fill="${dimCol}" font-family="monospace" font-size="6" font-weight="bold" text-anchor="middle">PULSE</text>
          <line x1="16" y1="18" x2="104" y2="18" stroke="${lineCol}" stroke-width="1"/>

          <text x="60" y="44" fill="${accentColor}" font-family="monospace" font-size="24" font-weight="900" text-anchor="middle" letter-spacing="-1">28</text>

          <g transform="translate(20, 50)">
            ${Array.from({ length: 18 }, (_, i) => `<circle cx="${i * 4.4 + 1}" cy="2" r="1.3" fill="${i < 5 ? accentColor : dotOff}"/>`).join('')}
          </g>

          <line x1="16" y1="58" x2="104" y2="58" stroke="${lineCol}" stroke-width="1"/>
          <text x="60" y="72" fill="${dimCol}" font-family="monospace" font-size="7" font-weight="bold" text-anchor="middle">LOAD</text>
        </svg>
      `;
  }
}
