const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// Import the html2pptx library
const { chromium } = require('playwright');
const sharp = require('sharp');

// Helper functions
const PT_PER_PX = 0.75;
const PX_PER_IN = 96;
const EMU_PER_IN = 914400;

async function getBodyDimensions(page) {
  const bodyDimensions = await page.evaluate(() => {
    const body = document.body;
    const style = window.getComputedStyle(body);
    return {
      width: parseFloat(style.width),
      height: parseFloat(style.height),
      scrollWidth: body.scrollWidth,
      scrollHeight: body.scrollHeight
    };
  });

  const errors = [];
  // Check for overflow
  if (bodyDimensions.scrollWidth > bodyDimensions.width + 1) {
    errors.push(`Content overflows horizontally by ${(bodyDimensions.scrollWidth - bodyDimensions.width).toFixed(2)}px`);
  }
  if (bodyDimensions.scrollHeight > bodyDimensions.height + 1) {
    errors.push(`Content overflows vertically by ${(bodyDimensions.scrollHeight - bodyDimensions.height).toFixed(2)}px`);
  }

  return { ...bodyDimensions, errors };
}

async function extractHtmlElements(page) {
  return await page.evaluate(() => {
    const elements = [];
    const body = document.body;
    
    // Helper function to extract text content and style
    function extractText(element) {
      const text = element.textContent || element.innerText || '';
      if (!text.trim()) return null;
      
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      
      // Check if this is a text element (not just div)
      if (element.tagName === 'P' || element.tagName.startsWith('H') || 
          element.tagName === 'UL' || element.tagName === 'OL' ||
          (element.tagName === 'DIV' && text.trim())) {
        
        // Get CSS properties
        const cssProps = {
          'font-family': style.fontFamily,
          'font-size': style.fontSize,
          'font-weight': style.fontWeight,
          'color': style.color,
          'text-align': style.textAlign,
          'margin': style.margin,
          'padding': style.padding
        };

        return {
          type: 'text',
          tagName: element.tagName,
          text: text.trim(),
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
          cssProps: cssProps,
          isBold: style.fontWeight === 'bold' || parseInt(style.fontWeight) >= 600,
          isItalic: style.fontStyle === 'italic',
          color: style.color,
          fontSize: style.fontSize,
          textAlign: style.textAlign
        };
      }
      
      return null;
    }

    // Get all text elements
    const textElements = body.querySelectorAll('p, h1, h2, h3, h4, h5, h6, ul, ol, div');
    textElements.forEach(element => {
      const textEl = extractText(element);
      if (textEl) {
        elements.push(textEl);
      }
    });

    // Get all shape elements (divs with background or border)
    const shapeElements = body.querySelectorAll('div');
    shapeElements.forEach(element => {
      const style = window.getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      
      // Check if it has styling that makes it a shape
      if (style.background !== 'rgba(0, 0, 0, 0)' || 
          style.border !== 'none' || 
          style.backgroundColor !== 'rgba(0, 0, 0, 0)') {
        
        elements.push({
          type: 'shape',
          tagName: 'DIV',
          left: rect.left,
          top: rect.top,
          width: rect.width,
          height: rect.height,
          cssProps: {
            'background': style.background,
            'background-color': style.backgroundColor,
            'border': style.border,
            'border-radius': style.borderRadius,
            'box-shadow': style.boxShadow
          }
        });
      }
    });

    return elements;
  });
}

// Simple html2pptx conversion function
async function convertHtmlToPptx(htmlFile, pptx, options = {}) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 960, height: 540 } // 16:9 aspect ratio
  });
  const page = await context.newPage();

  try {
    // Load HTML file
    const htmlContent = fs.readFileSync(htmlFile, 'utf-8');
    const pageUrl = `data:text/html;charset=utf-8,${encodeURIComponent(htmlContent)}`;
    await page.goto(pageUrl);

    // Wait for content to load
    await page.waitForTimeout(1000);

    // Get body dimensions
    const bodyDim = await getBodyDimensions(page);
    if (bodyDim.errors.length > 0) {
      console.warn(`HTML validation warnings for ${htmlFile}:`, bodyDim.errors);
    }

    // Extract elements
    const elements = await extractHtmlElements(page);
    
    // Convert to PowerPoint
    const slide = pptx.addSlide();
    
    // Add elements to slide
    for (const element of elements) {
      if (element.type === 'text') {
        try {
          // Parse font size
          const fontSize = element.fontSize ? parseFloat(element.fontSize) * PT_PER_PX : 12;
          const fontWeight = element.isBold ? 'bold' : 'normal';
          const fontStyle = element.isItalic ? 'italic' : 'normal';
          
          // Parse color (remove 'rgba(' and ')')
          let color = '000000';
          if (element.color) {
            const match = element.color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
            if (match) {
              color = parseInt(match[1]).toString(16).padStart(2, '0') +
                     parseInt(match[2]).toString(16).padStart(2, '0') +
                     parseInt(match[3]).toString(16).padStart(2, '0');
            }
          }
          
          // Calculate position in PowerPoint units
          const x = element.left / PX_PER_IN;
          const y = element.top / PX_PER_IN;
          const w = element.width / PX_PER_IN;
          const h = element.height / PX_PER_IN;
          
          // Add text
          slide.addText(element.text, {
            x: x,
            y: y,
            w: w,
            h: h,
            fontSize: fontSize,
            fontFace: 'Arial',
            bold: element.isBold,
            italic: element.isItalic,
            color: color,
            align: element.textAlign || 'left',
            valign: 'top'
          });
          
        } catch (error) {
          console.warn(`Error adding text element: ${error.message}`);
        }
      }
      else if (element.type === 'shape') {
        try {
          // Calculate position in PowerPoint units
          const x = element.left / PX_PER_IN;
          const y = element.top / PX_PER_IN;
          const w = element.width / PX_PER_IN;
          const h = element.height / PX_PER_IN;
          
          // Parse background color
          let fillColor = 'FFFFFF';
          const bgProp = element.cssProps['background-color'];
          if (bgProp && bgProp !== 'rgba(0, 0, 0, 0)') {
            const match = bgProp.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
            if (match) {
              fillColor = parseInt(match[1]).toString(16).padStart(2, '0') +
                         parseInt(match[2]).toString(16).padStart(2, '0') +
                         parseInt(match[3]).toString(16).padStart(2, '0');
            }
          }
          
          // Add shape (using rectangle as fallback)
          slide.addShape(pptx.shapes.RECTANGLE, {
            x: x,
            y: y,
            w: w,
            h: h,
            fill: { color: fillColor },
            line: { color: '000000', width: 0 }
          });
          
        } catch (error) {
          console.warn(`Error adding shape element: ${error.message}`);
        }
      }
    }

    await browser.close();
    return { slide, elements };

  } catch (error) {
    await browser.close();
    throw error;
  }
}

async function createZenMcpPresentation() {
    const pptx = new pptxgen();
    pptx.layout = 'LAYOUT_16x9';  // 10" x 5.625" (960px x 540px)
    pptx.author = 'Zen MCP Server Team';
    pptx.title = 'Zen MCP: Many Workflows. One Context.';
    pptx.subject = 'Complete Introduction to Zen MCP Server';
    pptx.company = 'Beehive Innovations';

    const slidesDir = path.join(__dirname, 'slides');
    const slideFiles = [
        'slide01-title.html',
        'slide02-overview.html', 
        'slide03-value-proposition.html',
        'slide04-architecture.html',
        'slide05-clink.html',
        'slide06-models.html',
        'slide07-workflows.html',
        'slide08-tools.html',
        'slide09-quickstart.html',
        'slide10-advanced-cases.html',
        'slide11-ecosystem.html',
        'slide12-conclusion.html'
    ];

    console.log('🎯 开始创建 Zen MCP 完整演示文稿...');

    for (let i = 0; i < slideFiles.length; i++) {
        const slideFile = path.join(slidesDir, slideFiles[i]);
        const slideNum = i + 1;
        
        console.log(`📄 转换幻灯片 ${slideNum}: ${slideFiles[i]}`);
        
        try {
            if (!fs.existsSync(slideFile)) {
                console.warn(`⚠️ 文件不存在: ${slideFile}`);
                continue;
            }

            const { slide, elements } = await convertHtmlToPptx(slideFile, pptx);
            
            // Add slide number at bottom right
            slide.addText(`${slideNum} / ${slideFiles.length}`, {
                x: 9, y: 5.2, w: 0.8, h: 0.3,
                fontSize: 12, fontFace: 'Arial', 
                color: '40695B', align: 'center', valign: 'bottom'
            });

            console.log(`✅ 幻灯片 ${slideNum} 转换完成 (${elements.length} 个元素)`);

        } catch (error) {
            console.error(`❌ 处理幻灯片 ${slideNum} 时出错:`, error.message);
        }
    }

    // Save to workspace root
    const outputPath = path.join(process.cwd(), 'zen-mcp-presentation.pptx');
    
    try {
        await pptx.writeFile({ fileName: outputPath });
        console.log(`🎉 完整演示文稿创建成功！`);
        console.log(`📁 文件位置: ${outputPath}`);
        console.log(`📊 总共 ${slideFiles.length} 张幻灯片`);
        
        return outputPath;
    } catch (error) {
        console.error('❌ 创建演示文稿失败:', error.message);
        throw error;
    }
}

// Execute conversion
if (require.main === module) {
    createZenMcpPresentation()
        .then(outputFile => {
            console.log('✅ HTML到PowerPoint转换完成:', outputFile);
        })
        .catch(error => {
            console.error('❌ 转换失败:', error);
            process.exit(1);
        });
}

module.exports = { createZenMcpPresentation, convertHtmlToPptx };