import React, { useState, useEffect } from 'react';
import { 
  Gavel, 
  Download, 
  User, 
  AlertCircle, 
  CheckCircle2, 
  BookOpen, 
  LayoutTemplate, 
  CreditCard, 
  ChevronRight,
  MousePointerClick,
  Info
} from 'lucide-react';

const LegallyApp = () => {
  const [activeIssue, setActiveIssue] = useState(null);
  const [score, setScore] = useState(7.2);

  // Данные об ошибках (Mock Data based on screenshots)
  const issues = [
    {
      id: 'case-num',
      type: 'structure',
      severity: 'medium',
      textInDoc: 'Дело № 1-1111/1111 ~ М-1111/1111',
      title: 'Структура документа',
      description: 'Вводная конструкция утяжеляет текст. Эту информацию лучше вынести в шапку для быстрого сканирования (Legal Design).',
      suggestion: 'Перенести в шапку (метаданные)',
      link: '#',
      color: 'bg-yellow-100 border-yellow-300 text-yellow-800'
    },
    {
      id: 'grammar-case',
      type: 'grammar',
      severity: 'high',
      textInDoc: 'в порядке наследования к Цой К. П.',
      title: 'Смысловая/Грамматическая ошибка',
      description: 'Несуществующая правовая конструкция. Право собственности признается «в порядке наследования», предлог «к» здесь создает двусмысленность.',
      suggestion: '...в порядке наследования',
      link: '#',
      color: 'bg-red-100 border-red-300 text-red-800'
    },
    {
      id: 'readability-long',
      type: 'readability',
      severity: 'high',
      textInDoc: 'По смыслу данной нормы... (весь абзац)',
      title: 'Сложная читаемость (Fog Index)',
      description: 'Предложение перегружено причастными оборотами и канцеляризмами. Индекс туманности Ганнинга > 18. Судье будет сложно уловить суть с первого прочтения.',
      suggestion: 'Разбить на 2 предложения и упростить формулировки.',
      link: '#',
      color: 'bg-red-50 border-red-200 text-red-900'
    },
    {
      id: 'typography-space',
      type: 'typography',
      severity: 'low',
      textInDoc: 'ст.420',
      title: 'Типографика',
      description: 'Отсутствует неразрывный пробел между знаком сокращения и цифрой. Это затрудняет чтение и выглядит непрофессионально.',
      suggestion: 'ст. 420',
      link: '#',
      color: 'bg-orange-100 border-orange-300 text-orange-800'
    },
    {
      id: 'logic-proshu',
      type: 'logic',
      severity: 'medium',
      textInDoc: 'ПРОШУ:',
      title: 'Нарушение логики',
      description: 'Слово «ПРОШУ» здесь неуместно, так как далее следует мотивировочный вывод, а не просительная часть.',
      suggestion: 'Удалить заголовок',
      link: '#',
      color: 'bg-yellow-100 border-yellow-300 text-yellow-800'
    }
  ];

  // Компонент для выделения текста
  const Highlight = ({ id, children, className = "" }) => {
    const issue = issues.find(i => i.id === id);
    const isActive = activeIssue === id;
    
    // Базовые стили для разных типов ошибок
    let baseStyle = "cursor-pointer transition-all duration-200 border-b-2 ";
    if (issue?.severity === 'high') baseStyle += "bg-red-50 border-red-400 hover:bg-red-100";
    else if (issue?.severity === 'medium') baseStyle += "bg-yellow-50 border-yellow-400 hover:bg-yellow-100";
    else baseStyle += "bg-orange-50 border-orange-300 hover:bg-orange-100";

    // Стиль при активации
    const activeStyle = isActive ? " ring-2 ring-offset-1 ring-indigo-500 rounded px-0.5" : "";

    return (
      <span 
        className={`${baseStyle} ${activeStyle} ${className}`}
        onClick={() => setActiveIssue(id)}
        title={issue?.title}
      >
        {children}
      </span>
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800 flex flex-col">
      
      {/* --- HEADER --- */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg text-white">
              <Gavel size={20} />
            </div>
            <div>
              <h1 className="font-bold text-lg leading-tight tracking-tight">Legally</h1>
              <p className="text-[10px] text-slate-400 uppercase tracking-wider font-semibold">Юридический редактор</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-500">
            <a href="#" className="text-indigo-600 border-b-2 border-indigo-600 py-5">Проверка</a>
            <a href="#" className="hover:text-slate-800 transition-colors">Справочник</a>
            <a href="#" className="hover:text-slate-800 transition-colors">Шаблоны</a>
            <a href="#" className="hover:text-slate-800 transition-colors">Тарифы</a>
          </nav>

          {/* User Actions */}
          <div className="flex items-center gap-6">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-semibold text-slate-700">Иван Петров</p>
              <p className="text-xs text-slate-400">Free Plan</p>
            </div>
            <button className="bg-slate-900 hover:bg-slate-800 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors">
              <Download size={16} />
              Экспорт
            </button>
          </div>
        </div>
      </header>

      {/* --- MAIN CONTENT --- */}
      <main className="flex-1 max-w-[1600px] mx-auto w-full grid grid-cols-12 gap-8 p-6">
        
        {/* --- LEFT: DOCUMENT EDITOR --- */}
        <div className="col-span-12 lg:col-span-8">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 min-h-[800px] p-12 relative">
            
            {/* Paper texture/look */}
            <div className="max-w-[800px] mx-auto leading-relaxed text-[15px] text-slate-800 font-serif">
              
              {/* Header Info */}
              <div className="grid grid-cols-2 gap-8 mb-8 text-sm font-sans text-slate-600">
                <div></div>
                <div className="text-right space-y-1">
                  <p className="font-bold text-slate-900">В Кыштымский городской суд</p>
                  <p className="font-bold text-slate-900 mb-4">Челябинской области</p>
                  
                  <p><span className="font-semibold text-slate-800">Истец:</span> Ким Петр Евгеньевич</p>
                  <p className="text-slate-500 border-b border-indigo-100 bg-indigo-50/50 inline-block px-1">01.01.1962 года рождения</p>
                  <p>Место рождения: г. Челябинск</p>
                  <p>Адрес регистрации: 111111, г. Челябинск, ул. Труда, д. 7</p>
                  <p>Адрес для корреспонденции: 111111, г. Челябинск, ул. Маркса, д.5</p>
                  
                  <div className="mt-4">
                    <p><span className="font-semibold text-slate-800">Представитель истца по доверенности:</span></p>
                    <p>Кум Валентина Андреевна</p>
                    <p>Адрес для корреспонденции: 111111, г. Челябинск, ул. Маркса, д. 3</p>
                  </div>

                  <p className="mt-4"><span className="font-semibold text-slate-800">Ответчик:</span> Цой К.П.</p>
                </div>
              </div>

              {/* Document Body */}
              <div className="text-center mb-8 space-y-4">
                 <div className="flex justify-center mb-6">
                    <Highlight id="case-num" className="font-bold text-slate-900">
                      Дело № 1-1111/1111 ~ М-1111/1111
                    </Highlight>
                 </div>

                 <h2 className="text-xl font-bold uppercase tracking-wide">Возражение</h2>
                 <p className="text-slate-500 italic">на исковое заявление</p>
              </div>

              <div className="space-y-6 text-justify">
                <p>
                  В производстве Кыштымского городского суда Челябинской области находится дело № 1-1111/1111 по исковому заявлению Ким П.Е. (далее – Истец) о включении имущества в наследственную массу и признании права собственности <Highlight id="grammar-case">в порядке наследования к Цой К. П.</Highlight> (далее – Ответчик).
                </p>

                <p>В своих исковых требованиях Истец просит суд:</p>
                
                <ul className="list-disc pl-5 space-y-2">
                  <li>Включить имущество: гараж, расположенный на земельном участке по адресу: Челябинская обл., г. Карабаш, ДНТ «Солнце-1», уч. 38, к/н 11:11:1111111:111 в наследственную массу наследодателя Цой Е.Ю., умершего 05.04.2023 г.</li>
                  <li>Признать право собственности истца на указанное имущество в порядке наследодателя.</li>
                </ul>

                <p>Ответчик возражает против удовлетворения указанных исковых требований, предоставляя следующие доводы.</p>

                <p>Между Цой Е. Ю. и Цой К. П. 25.03.2023 года был заключен договор дарения, согласно которому Цой Е. Ю. безвозмездно передал, а Цой К.П. приняла в дар недвижимое имущество, состоящее из земельного участка по адресу: Челябинская обл., г. Карабаш, ДНТ «Солнце-1», уч. 38, к/н 11:11:1111111:111.</p>

                <p>Согласно статье 1 Гражданского кодекса Российской Федерации при установлении, осуществлении и защите гражданских прав и при исполнении гражданских обязанностей участники гражданских правоотношений должны действовать добросовестно. В статье 10 данного Кодекса закреплена недопустимость действий граждан и юридических лиц, осуществляемых исключительно с намерением причинить вред другому лицу, а также злоупотребление правом в иных формах. По смыслу приведенных норм права, добросовестность при осуществлении гражданских прав и при исполнении гражданских обязанностей предполагает поведение, ожидаемое от любого участника гражданского оборота, учитывающего права и законные интересы другой стороны, содействующее ей (пункт 1 постановления Пленума Верховного Суда Российской Федерации).</p>

                <p>Согласно <Highlight id="typography-space">ст.420</Highlight> ГК РФ граждане и юридические лица свободны в заключении договора.</p>

                <p>В соответствии со ст.56 ГК РФ каждая сторона должна доказать те обстоятельства, на которые она ссылается как на основания своих требований и возражений.</p>

                <p>Каждое лицо, участвующее в деле, должно раскрыть доказательства, на которые оно ссылается как на основание своих требований и возражений, перед другими лицами, участвующими в деле, в пределах срока, установленного судом.</p>

                <p>Принцип свободы заключения договора нарушен не был, доводы Истца об «убеждении» дарителя ничтожен без каких-либо доказательств. Данный объект недвижимости имеет государственную регистрацию, что подтверждается выпиской из ЕГРН на объект недвижимости.</p>

                <p>Согласно ст. 35 Земельного кодекса РФ не допускается отчуждение земельного участка без находящихся на нем здания, сооружения в случае, если они принадлежат одному лицу.</p>

                <Highlight id="readability-long" className="block p-1">
                  По смыслу данной нормы, при отчуждении земельного участка в случае, если на нем находятся объекты недвижимого имущества, то они право собственности переходит не только на земельный участок, но на здания и сооружения, находящиеся на данном земельном участке
                </Highlight>

                <p>Таким образом, исковые требования Истца не подлежат удовлетворению, так как право собственности на данный земельный участок и на все объекты недвижимого имущества принадлежит Ответчику на законных основаниях.</p>

                <p>На основании изложенного,</p>

                <Highlight id="logic-proshu" className="font-bold uppercase block mt-6 mb-2">ПРОШУ:</Highlight>

                <p>Таким образом, доводы и доказательства Цой Е. Ю. прошу считать ничтожными. Исковые требования прошу признать не подлежащими удовлетворению.</p>

                <div>
                  <p className="font-bold mb-2">Приложение:</p>
                  <ul className="list-disc pl-5 space-y-1 text-slate-700">
                    <li className="underline decoration-orange-300 decoration-wavy underline-offset-2">Почтовые документы, подтверждающие возражения ответчику</li>
                    <li>Копия паспорта</li>
                    <li>Копия договора дарения</li>
                    <li>Копии выписок из ЕГРН</li>
                  </ul>
                </div>
                
                <div className="flex justify-between items-end mt-12 pt-8 border-t border-slate-100">
                    <div>«_____» _____________ 2023 г.</div>
                    <div>_____________/К.П.Цой</div>
                </div>

              </div>
            </div>
          </div>
        </div>

        {/* --- RIGHT: SIDEBAR --- */}
        <div className="col-span-12 lg:col-span-4 space-y-6">
          
          {/* Score Card */}
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">Качество документа</h3>
                <span className="text-[10px] font-bold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-full flex items-center gap-1">
                    <BookOpen size={12} /> Legal Design
                </span>
            </div>
            
            <div className="flex items-center gap-6">
                {/* CSS Circle Chart Mock */}
                <div className="relative w-20 h-20 flex items-center justify-center rounded-full border-4 border-slate-100">
                    <svg className="absolute top-0 left-0 w-full h-full transform -rotate-90">
                        <circle cx="50%" cy="50%" r="36" fill="transparent" stroke="#4f46e5" strokeWidth="4" strokeDasharray="226" strokeDashoffset="60" strokeLinecap="round" />
                    </svg>
                    <div className="text-center">
                        <span className="block text-2xl font-bold text-slate-800">{score}</span>
                        <span className="block text-[9px] text-slate-400">из 10</span>
                    </div>
                </div>
                
                <div>
                    <p className="font-bold text-slate-800">Есть риски</p>
                    <p className="text-xs text-slate-500 mt-1">Обнаружено <span className="text-red-500 font-semibold">3 грубых ошибки</span>.</p>
                    <p className="text-xs text-slate-400 mt-1">Рекомендуем исправить перед отправкой.</p>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-slate-100 mt-6">
                <button className="flex-1 pb-3 text-sm font-medium text-indigo-600 border-b-2 border-indigo-600">Все (5)</button>
                <button className="flex-1 pb-3 text-sm font-medium text-slate-400 hover:text-slate-600">Ошибки</button>
                <button className="flex-1 pb-3 text-sm font-medium text-slate-400 hover:text-slate-600">Стиль</button>
            </div>
          </div>

          {/* Issue Details / List */}
          <div className="space-y-4">
            
            {activeIssue ? (
               /* --- ACTIVE ISSUE CARD --- */
               (() => {
                 const issue = issues.find(i => i.id === activeIssue);
                 return (
                   <div className="bg-white rounded-xl shadow-md border-l-4 border-indigo-500 border-y border-r border-slate-200 p-5 transition-all animate-in fade-in slide-in-from-right-4 duration-300">
                      <div className="flex justify-between items-start mb-2">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                            issue.type === 'structure' ? 'bg-yellow-100 text-yellow-700' :
                            issue.type === 'grammar' ? 'bg-red-100 text-red-700' :
                            'bg-slate-100 text-slate-600'
                        }`}>
                            {issue.type}
                        </span>
                        <button onClick={() => setActiveIssue(null)} className="text-slate-400 hover:text-slate-600">×</button>
                      </div>
                      
                      <h4 className="font-bold text-slate-800 text-sm mb-2">{issue.title}</h4>
                      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
                        {issue.description}
                      </p>
                      
                      {/* Suggestion Box */}
                      <div className="bg-green-50 border border-green-100 rounded-lg p-3 mb-4">
                         <div className="flex items-center gap-2 text-xs font-semibold text-green-700 mb-1">
                            <CheckCircle2 size={12} /> Рекомендация:
                         </div>
                         <p className="text-sm text-slate-800 font-medium">{issue.suggestion}</p>
                      </div>

                      {/* Links */}
                      <div className="mb-4">
                        <a href="#" className="flex items-center gap-1 text-xs text-indigo-600 hover:underline">
                             <Info size={12} /> Справка: Правила оформления исков
                        </a>
                      </div>

                      {/* Actions */}
                      <div className="flex gap-2">
                          <button 
                            className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold py-2 rounded transition-colors shadow-sm shadow-indigo-200"
                            onClick={() => {
                                setScore(prev => Math.min(prev + 0.5, 10).toFixed(1));
                                setActiveIssue(null);
                            }}
                          >
                            Применить
                          </button>
                          <button className="px-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-500 text-xs font-bold rounded transition-colors">
                            Игнор.
                          </button>
                      </div>
                   </div>
                 );
               })()
            ) : (
                /* --- DEFAULT LIST VIEW --- */
                issues.map((issue) => (
                    <div 
                        key={issue.id} 
                        onClick={() => setActiveIssue(issue.id)}
                        className={`bg-white rounded-xl border border-slate-200 p-4 cursor-pointer hover:shadow-md transition-all hover:border-indigo-200 group relative overflow-hidden`}
                    >
                        <div className={`absolute left-0 top-0 bottom-0 w-1 ${
                            issue.severity === 'high' ? 'bg-red-400' : 
                            issue.severity === 'medium' ? 'bg-yellow-400' : 'bg-orange-300'
                        }`}></div>
                        
                        <div className="pl-2">
                            <h4 className="font-semibold text-sm text-slate-800 mb-1 group-hover:text-indigo-700 transition-colors">
                                {issue.title}
                            </h4>
                            <p className="text-xs text-slate-400 line-clamp-2 mb-2">
                                {issue.description}
                            </p>
                            <div className="bg-slate-50 p-2 rounded text-xs text-slate-600 font-mono border border-slate-100 truncate">
                                → {issue.suggestion}
                            </div>
                        </div>
                    </div>
                ))
            )}

            {/* Helper Hint */}
            {!activeIssue && (
                <div className="text-center p-4 text-xs text-slate-400 flex flex-col items-center gap-2 border-2 border-dashed border-slate-200 rounded-xl">
                    <MousePointerClick size={16} />
                    Нажмите на выделенный текст или карточку, чтобы увидеть детали исправления.
                </div>
            )}

          </div>
        </div>

      </main>
    </div>
  );
};

export default LegallyApp;